from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from voiceforge_core.db.enums import EngineBackend, VoiceProfileStatus


class VoiceProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    preferred_backend: EngineBackend = EngineBackend.SEED_VC
    consent_confirmed: bool
    consent_text: str = Field(min_length=10)
    consent_evidence_storage_key: str | None = None


class VoiceProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    preferred_backend: EngineBackend
    status: VoiceProfileStatus
    consent_confirmed: bool
    total_duration_seconds: float
    clip_count: int
    noise_score: float
    diversity_score: float
    sample_rate: int
    readiness_score: float
    created_at: datetime
    updated_at: datetime

