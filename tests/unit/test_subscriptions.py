"""Tests for SubscriptionService — plan management, quotas, usage tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from voiceforge_core.db.enums import SubscriptionPlan, SubscriptionStatus, UserRole
from voiceforge_core.db.models import Subscription, UsageCounter, User, VoiceProfile
from voiceforge_core.modules.subscriptions.service import PLAN_LIMITS, SubscriptionService


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _make_user(session: Session, email: str = "sub@test.dev") -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        display_name="Sub Tester",
        password_hash="x" * 128,
        role=UserRole.USER,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _make_subscription(
    session: Session,
    user: User,
    plan: SubscriptionPlan = SubscriptionPlan.PRO,
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    days_remaining: int = 15,
) -> Subscription:
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user.id,
        plan=plan,
        status=status,
        current_period_start=now - timedelta(days=15),
        current_period_end=now + timedelta(days=days_remaining),
    )
    session.add(sub)
    session.flush()
    return sub


def _make_profile(session: Session, user: User) -> VoiceProfile:
    profile = VoiceProfile(
        user_id=user.id,
        name=f"Profile {uuid.uuid4().hex[:6]}",
        consent_confirmed=True,
        consent_text="I agree",
    )
    session.add(profile)
    session.flush()
    return profile


# ---------------------------------------------------------------------------
#  get_user_plan
# ---------------------------------------------------------------------------

class TestGetUserPlan:
    def test_no_subscription_returns_free(self, db_session: Session) -> None:
        user = _make_user(db_session)
        plan, status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.FREE
        assert status == SubscriptionStatus.ACTIVE

    def test_active_pro_subscription(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.PRO)
        plan, status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.PRO
        assert status == SubscriptionStatus.ACTIVE

    def test_active_unlimited_subscription(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.UNLIMITED)
        plan, status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.UNLIMITED

    def test_expired_subscription_returns_free(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, days_remaining=-1)
        plan, _status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.FREE

    def test_cancelled_within_period_keeps_plan(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(
            db_session, user,
            status=SubscriptionStatus.CANCELLED,
            days_remaining=10,
        )
        plan, status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.PRO
        assert status == SubscriptionStatus.CANCELLED

    def test_past_due_within_grace_keeps_plan(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = _make_subscription(
            db_session, user,
            status=SubscriptionStatus.PAST_DUE,
            days_remaining=-1,
        )
        sub.grace_period_end = datetime.now(timezone.utc) + timedelta(days=2)
        db_session.flush()
        plan, status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.PRO
        assert status == SubscriptionStatus.PAST_DUE

    def test_past_due_after_grace_downgrades(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = _make_subscription(
            db_session, user,
            status=SubscriptionStatus.PAST_DUE,
            days_remaining=-1,
        )
        sub.grace_period_end = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.flush()
        plan, _status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.FREE


# ---------------------------------------------------------------------------
#  Conversion quota
# ---------------------------------------------------------------------------

class TestConversionQuota:
    def test_free_user_has_3_conversions(self, db_session: Session) -> None:
        user = _make_user(db_session)
        assert SubscriptionService.check_conversion_quota(db_session, user.id) is True

        # Use all 3
        for _ in range(3):
            SubscriptionService.increment_usage(db_session, user.id)

        assert SubscriptionService.check_conversion_quota(db_session, user.id) is False

    def test_pro_user_has_50_conversions(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.PRO)
        assert SubscriptionService.check_conversion_quota(db_session, user.id) is True

    def test_unlimited_user_never_blocked(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.UNLIMITED)
        # Simulate heavy usage
        counter = SubscriptionService._get_or_create_counter(db_session, user.id)
        counter.conversions_used = 9999
        db_session.flush()
        assert SubscriptionService.check_conversion_quota(db_session, user.id) is True

    def test_increment_usage_returns_new_total(self, db_session: Session) -> None:
        user = _make_user(db_session)
        assert SubscriptionService.increment_usage(db_session, user.id) == 1
        assert SubscriptionService.increment_usage(db_session, user.id) == 2


# ---------------------------------------------------------------------------
#  Profile quota
# ---------------------------------------------------------------------------

class TestProfileQuota:
    def test_free_user_limited_to_1_profile(self, db_session: Session) -> None:
        user = _make_user(db_session)
        assert SubscriptionService.check_profile_quota(db_session, user.id) is True
        _make_profile(db_session, user)
        assert SubscriptionService.check_profile_quota(db_session, user.id) is False

    def test_pro_user_limited_to_5_profiles(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.PRO)
        for _ in range(5):
            _make_profile(db_session, user)
        assert SubscriptionService.check_profile_quota(db_session, user.id) is False

    def test_unlimited_user_no_limit(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.UNLIMITED)
        for _ in range(10):
            _make_profile(db_session, user)
        assert SubscriptionService.check_profile_quota(db_session, user.id) is True


# ---------------------------------------------------------------------------
#  Subscription lifecycle
# ---------------------------------------------------------------------------

class TestSubscriptionLifecycle:
    def test_activate_creates_new_subscription(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = SubscriptionService.activate_subscription(
            db_session, user.id, SubscriptionPlan.PRO, payment_reference="ref-123"
        )
        assert sub.plan == SubscriptionPlan.PRO
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.payment_reference == "ref-123"

    def test_activate_extends_existing(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub1 = SubscriptionService.activate_subscription(
            db_session, user.id, SubscriptionPlan.PRO
        )
        original_end = sub1.current_period_end
        sub2 = SubscriptionService.activate_subscription(
            db_session, user.id, SubscriptionPlan.PRO
        )
        assert sub2.id == sub1.id  # Same record extended
        assert sub2.current_period_end > original_end

    def test_cancel_keeps_active_until_period_end(self, db_session: Session) -> None:
        user = _make_user(db_session)
        sub = SubscriptionService.activate_subscription(
            db_session, user.id, SubscriptionPlan.PRO
        )
        cancelled = SubscriptionService.cancel_subscription(db_session, user.id)
        assert cancelled is not None
        assert cancelled.status == SubscriptionStatus.CANCELLED
        assert cancelled.cancelled_at is not None
        # Plan still active within period
        plan, _status = SubscriptionService.get_user_plan(db_session, user.id)
        assert plan == SubscriptionPlan.PRO

    def test_cancel_nonexistent_returns_none(self, db_session: Session) -> None:
        user = _make_user(db_session)
        result = SubscriptionService.cancel_subscription(db_session, user.id)
        assert result is None

    def test_mark_past_due_sets_grace_period(self, db_session: Session) -> None:
        user = _make_user(db_session)
        SubscriptionService.activate_subscription(db_session, user.id, SubscriptionPlan.PRO)
        sub = SubscriptionService.mark_past_due(db_session, user.id)
        assert sub is not None
        assert sub.status == SubscriptionStatus.PAST_DUE
        assert sub.grace_period_end is not None


# ---------------------------------------------------------------------------
#  Usage summary
# ---------------------------------------------------------------------------

class TestUsageSummary:
    def test_summary_for_free_user(self, db_session: Session) -> None:
        user = _make_user(db_session)
        SubscriptionService.increment_usage(db_session, user.id)
        summary = SubscriptionService.get_usage_summary(db_session, user.id)
        assert summary.plan == SubscriptionPlan.FREE
        assert summary.conversions_used == 1
        assert summary.conversions_limit == 3
        assert summary.conversions_remaining == 2
        assert summary.profiles_limit == 1

    def test_summary_for_unlimited_user(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.UNLIMITED)
        summary = SubscriptionService.get_usage_summary(db_session, user.id)
        assert summary.plan == SubscriptionPlan.UNLIMITED
        assert summary.conversions_limit == -1
        assert summary.conversions_remaining == -1
        assert summary.profiles_limit == -1


# ---------------------------------------------------------------------------
#  Watermark check
# ---------------------------------------------------------------------------

class TestWatermark:
    def test_free_user_requires_watermark(self, db_session: Session) -> None:
        user = _make_user(db_session)
        assert SubscriptionService.requires_watermark(db_session, user.id) is True

    def test_pro_user_no_watermark(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _make_subscription(db_session, user, SubscriptionPlan.PRO)
        assert SubscriptionService.requires_watermark(db_session, user.id) is False
