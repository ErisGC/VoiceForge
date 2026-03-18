"""Subscription and usage quota management service.

Handles plan verification, usage tracking, and subscription lifecycle
for the freemium model (Free / Pro / Unlimited).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from voiceforge_core.db.enums import SubscriptionPlan, SubscriptionStatus
from voiceforge_core.db.models import Subscription, UsageCounter, VoiceProfile

logger = logging.getLogger("voiceforge.subscriptions")


def _utcnow() -> datetime:
    """Return the current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (SQLite returns naive datetimes)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# Plan limits — single source of truth for the backend.
PLAN_LIMITS: dict[SubscriptionPlan, dict[str, int]] = {
    SubscriptionPlan.FREE: {"conversions_per_month": 3, "max_profiles": 1},
    SubscriptionPlan.PRO: {"conversions_per_month": 50, "max_profiles": 5},
    SubscriptionPlan.UNLIMITED: {"conversions_per_month": -1, "max_profiles": -1},
}

GRACE_PERIOD_DAYS = 3


@dataclass(frozen=True, slots=True)
class UsageSummary:
    """Usage statistics for the current billing period."""

    plan: SubscriptionPlan
    status: SubscriptionStatus
    conversions_used: int
    conversions_limit: int
    conversions_remaining: int
    profiles_used: int
    profiles_limit: int
    period: str  # YYYY-MM
    period_start: datetime | None
    period_end: datetime | None


class SubscriptionService:
    """Static service for subscription and quota management."""

    @staticmethod
    def get_user_plan(session: Session, user_id: UUID) -> tuple[SubscriptionPlan, SubscriptionStatus]:
        """Return the active plan for a user, or (FREE, ACTIVE) by default.

        Checks for active or grace-period subscriptions. Expired or
        cancelled subscriptions past their period are ignored.
        """
        now = _utcnow()
        statement = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.PAST_DUE,
                    SubscriptionStatus.CANCELLED,
                ]),
            )
            .order_by(Subscription.current_period_end.desc())
            .limit(1)
        )
        sub = session.scalar(statement)

        if sub is None:
            return SubscriptionPlan.FREE, SubscriptionStatus.ACTIVE

        period_end = _ensure_aware(sub.current_period_end)

        # Active subscription within its period
        if sub.status == SubscriptionStatus.ACTIVE and period_end >= now:
            return sub.plan, sub.status

        # Cancelled but still within paid period
        if sub.status == SubscriptionStatus.CANCELLED and period_end >= now:
            return sub.plan, sub.status

        # Past due within grace period
        if sub.status == SubscriptionStatus.PAST_DUE:
            grace_end = _ensure_aware(sub.grace_period_end) if sub.grace_period_end else period_end
            if grace_end >= now:
                return sub.plan, sub.status
            # Grace period expired — downgrade
            sub.status = SubscriptionStatus.EXPIRED
            session.flush()
            logger.info(
                "subscription_expired",
                extra={"user_id": str(user_id), "plan": sub.plan.value},
            )

        return SubscriptionPlan.FREE, SubscriptionStatus.ACTIVE

    @staticmethod
    def _current_period() -> str:
        """Return the current billing period as YYYY-MM."""
        return _utcnow().strftime("%Y-%m")

    @staticmethod
    def _get_or_create_counter(session: Session, user_id: UUID) -> UsageCounter:
        """Get or create the usage counter for the current month."""
        period = SubscriptionService._current_period()
        statement = select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.period_month == period,
        )
        counter = session.scalar(statement)
        if counter is None:
            counter = UsageCounter(
                user_id=user_id,
                period_month=period,
                conversions_used=0,
            )
            session.add(counter)
            session.flush()
        return counter

    @staticmethod
    def check_conversion_quota(session: Session, user_id: UUID) -> bool:
        """Check if the user can perform another conversion this month."""
        plan, _status = SubscriptionService.get_user_plan(session, user_id)
        limits = PLAN_LIMITS[plan]
        if limits["conversions_per_month"] == -1:
            return True
        counter = SubscriptionService._get_or_create_counter(session, user_id)
        return counter.conversions_used < limits["conversions_per_month"]

    @staticmethod
    def increment_usage(session: Session, user_id: UUID) -> int:
        """Increment the conversion counter for the current month.

        Returns the new total conversions used.
        """
        counter = SubscriptionService._get_or_create_counter(session, user_id)
        counter.conversions_used += 1
        session.flush()
        logger.info(
            "usage_incremented",
            extra={
                "user_id": str(user_id),
                "period": counter.period_month,
                "conversions_used": counter.conversions_used,
            },
        )
        return counter.conversions_used

    @staticmethod
    def check_profile_quota(session: Session, user_id: UUID) -> bool:
        """Check if the user can create another voice profile."""
        plan, _status = SubscriptionService.get_user_plan(session, user_id)
        limits = PLAN_LIMITS[plan]
        if limits["max_profiles"] == -1:
            return True
        from sqlalchemy import func

        count = session.scalar(
            select(func.count(VoiceProfile.id)).where(VoiceProfile.user_id == user_id)
        )
        return (count or 0) < limits["max_profiles"]

    @staticmethod
    def get_usage_summary(session: Session, user_id: UUID) -> UsageSummary:
        """Build a complete usage summary for the current period."""
        plan, sub_status = SubscriptionService.get_user_plan(session, user_id)
        limits = PLAN_LIMITS[plan]
        counter = SubscriptionService._get_or_create_counter(session, user_id)

        from sqlalchemy import func
        profile_count = session.scalar(
            select(func.count(VoiceProfile.id)).where(VoiceProfile.user_id == user_id)
        ) or 0

        conv_limit = limits["conversions_per_month"]
        if conv_limit == -1:
            remaining = -1
        else:
            remaining = max(0, conv_limit - counter.conversions_used)

        # Find subscription period dates
        period_start: datetime | None = None
        period_end: datetime | None = None
        sub = session.scalar(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.CANCELLED,
                    SubscriptionStatus.PAST_DUE,
                ]),
            )
            .order_by(Subscription.current_period_end.desc())
            .limit(1)
        )
        if sub is not None:
            period_start = sub.current_period_start
            period_end = sub.current_period_end

        return UsageSummary(
            plan=plan,
            status=sub_status,
            conversions_used=counter.conversions_used,
            conversions_limit=conv_limit,
            conversions_remaining=remaining,
            profiles_used=profile_count,
            profiles_limit=limits["max_profiles"],
            period=counter.period_month,
            period_start=period_start,
            period_end=period_end,
        )

    @staticmethod
    def activate_subscription(
        session: Session,
        user_id: UUID,
        plan: SubscriptionPlan,
        payment_reference: str | None = None,
        wompi_transaction_id: str | None = None,
        period_days: int = 30,
    ) -> Subscription:
        """Create or renew a subscription for a user.

        If an active subscription exists, extends it from its current end.
        Otherwise creates a new one starting now.
        """
        now = _utcnow()

        # Deactivate any existing expired/old subscriptions
        session.execute(
            update(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.PAST_DUE,
                ]),
                Subscription.current_period_end < now,
            )
            .values(status=SubscriptionStatus.EXPIRED)
        )

        # Check for existing active subscription to extend
        existing = session.scalar(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        # Filter in Python to handle naive/aware datetime comparison (SQLite compat)
        if existing is not None and _ensure_aware(existing.current_period_end) < now:
            existing = None

        if existing is not None:
            # Extend from current period end
            existing.plan = plan
            existing.current_period_end = existing.current_period_end + timedelta(days=period_days)
            existing.wompi_transaction_id = wompi_transaction_id
            existing.payment_reference = payment_reference
            session.flush()
            logger.info(
                "subscription_renewed",
                extra={
                    "user_id": str(user_id),
                    "plan": plan.value,
                    "new_end": existing.current_period_end.isoformat(),
                },
            )
            return existing

        # Create new subscription
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=period_days),
            wompi_transaction_id=wompi_transaction_id,
            payment_reference=payment_reference,
        )
        session.add(sub)
        session.flush()
        logger.info(
            "subscription_activated",
            extra={
                "user_id": str(user_id),
                "plan": plan.value,
                "period_end": sub.current_period_end.isoformat(),
            },
        )
        return sub

    @staticmethod
    def cancel_subscription(session: Session, user_id: UUID) -> Subscription | None:
        """Cancel the user's active subscription.

        The subscription remains active until the end of the current period.
        After that, the user downgrades to Free automatically.
        """
        now = _utcnow()
        sub = session.scalar(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        if sub is None:
            return None
        if _ensure_aware(sub.current_period_end) < now:
            return None

        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = now
        session.flush()
        logger.info(
            "subscription_cancelled",
            extra={
                "user_id": str(user_id),
                "plan": sub.plan.value,
                "active_until": sub.current_period_end.isoformat(),
            },
        )
        return sub

    @staticmethod
    def mark_past_due(session: Session, user_id: UUID) -> Subscription | None:
        """Mark subscription as past due with grace period."""
        now = _utcnow()
        sub = session.scalar(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        if sub is None:
            return None

        sub.status = SubscriptionStatus.PAST_DUE
        sub.grace_period_end = now + timedelta(days=GRACE_PERIOD_DAYS)
        session.flush()
        logger.info(
            "subscription_past_due",
            extra={
                "user_id": str(user_id),
                "grace_until": sub.grace_period_end.isoformat(),
            },
        )
        return sub

    @staticmethod
    def requires_watermark(session: Session, user_id: UUID) -> bool:
        """Check if the user's output audio should have a watermark.

        Only free plan users get watermarked output.
        """
        plan, _status = SubscriptionService.get_user_plan(session, user_id)
        return plan == SubscriptionPlan.FREE
