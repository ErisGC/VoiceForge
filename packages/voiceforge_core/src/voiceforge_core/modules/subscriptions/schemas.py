"""Pydantic schemas for subscription API responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from voiceforge_core.db.enums import SubscriptionPlan, SubscriptionStatus


class UsageSummaryRead(BaseModel):
    """Usage summary returned to the client."""

    plan: SubscriptionPlan
    status: SubscriptionStatus
    conversions_used: int
    conversions_limit: int
    conversions_remaining: int
    profiles_used: int
    profiles_limit: int
    period: str
    period_start: datetime | None = None
    period_end: datetime | None = None


class QuotaCheckRead(BaseModel):
    """Quick quota check result."""

    allowed: bool
    plan: SubscriptionPlan
    used: int
    limit: int
    upgrade_url: str = "https://voiceforge.app/#precio"


class SubscriptionRead(BaseModel):
    """Subscription record."""

    model_config = {"from_attributes": True}

    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancelled_at: datetime | None = None
