"""Subscription and usage API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from voiceforge_core.db.enums import AuditEventType
from voiceforge_core.db.models import User
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.subscriptions.schemas import (
    QuotaCheckRead,
    SubscriptionRead,
    UsageSummaryRead,
)
from voiceforge_core.modules.subscriptions.service import (
    PLAN_LIMITS,
    SubscriptionService,
)

router = APIRouter()


@router.get("/usage", response_model=UsageSummaryRead)
def get_usage_summary(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> UsageSummaryRead:
    """Get usage summary for the current billing period."""
    summary = SubscriptionService.get_usage_summary(session, current_user.id)
    return UsageSummaryRead(
        plan=summary.plan,
        status=summary.status,
        conversions_used=summary.conversions_used,
        conversions_limit=summary.conversions_limit,
        conversions_remaining=summary.conversions_remaining,
        profiles_used=summary.profiles_used,
        profiles_limit=summary.profiles_limit,
        period=summary.period,
        period_start=summary.period_start,
        period_end=summary.period_end,
    )


@router.get("/can-convert", response_model=QuotaCheckRead)
def check_conversion_quota(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> QuotaCheckRead:
    """Check if the user can perform a conversion."""
    plan, _status = SubscriptionService.get_user_plan(session, current_user.id)
    limits = PLAN_LIMITS[plan]
    counter = SubscriptionService._get_or_create_counter(session, current_user.id)
    allowed = SubscriptionService.check_conversion_quota(session, current_user.id)
    return QuotaCheckRead(
        allowed=allowed,
        plan=plan,
        used=counter.conversions_used,
        limit=limits["conversions_per_month"],
    )


@router.get("/can-create-profile", response_model=QuotaCheckRead)
def check_profile_quota(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> QuotaCheckRead:
    """Check if the user can create another voice profile."""
    from sqlalchemy import func, select
    from voiceforge_core.db.models import VoiceProfile

    plan, _status = SubscriptionService.get_user_plan(session, current_user.id)
    limits = PLAN_LIMITS[plan]
    profile_count = session.scalar(
        select(func.count(VoiceProfile.id)).where(VoiceProfile.user_id == current_user.id)
    ) or 0
    allowed = SubscriptionService.check_profile_quota(session, current_user.id)
    return QuotaCheckRead(
        allowed=allowed,
        plan=plan,
        used=profile_count,
        limit=limits["max_profiles"],
    )


@router.post("/cancel", response_model=SubscriptionRead | None)
def cancel_subscription(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> SubscriptionRead | None:
    """Cancel the current subscription. Remains active until period end."""
    sub = SubscriptionService.cancel_subscription(session, current_user.id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )
    AuditService.record(
        session,
        user_id=current_user.id,
        actor_email=current_user.email,
        event_type=AuditEventType.SUBSCRIPTION_CANCELLED,
        entity_type="subscription",
        entity_id=str(sub.id),
        ip_address=request.client.host if request.client else None,
        payload={"plan": sub.plan.value, "active_until": sub.current_period_end.isoformat()},
    )
    session.commit()
    return SubscriptionRead.model_validate(sub)
