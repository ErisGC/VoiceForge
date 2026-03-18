from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from voiceforge_core.db.enums import ProcessingStatus, VoiceSampleSource


class VoiceSampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    voice_profile_id: UUID
    storage_bucket: str
    storage_key: str
    original_filename: str
    content_type: str
    size_bytes: int
    duration_seconds: float
    sample_rate: int
    channels: int
    source: VoiceSampleSource
    processing_status: ProcessingStatus
    noise_score: float
    diversity_score: float
    vad_segments: list[dict] | None
    created_at: datetime
    updated_at: datetime

