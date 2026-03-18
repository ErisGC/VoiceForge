from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from voiceforge_core.db.enums import ConversionMode, EngineBackend, JobStatus


class ConversionJobCreate(BaseModel):
    voice_profile_id: UUID
    backend: EngineBackend | None = None
    mode: ConversionMode = ConversionMode.STUDIO


class ConvertedAudioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversion_job_id: UUID
    storage_bucket: str
    storage_key: str
    format: str
    duration_seconds: float
    sample_rate: int
    size_bytes: int
    watermark_status: str
    traceability_metadata: dict | None
    created_at: datetime
    updated_at: datetime


class ConversionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    voice_profile_id: UUID
    backend: EngineBackend
    mode: ConversionMode
    status: JobStatus
    queue_name: str
    source_audio_bucket: str
    source_audio_storage_key: str
    source_audio_filename: str
    source_audio_content_type: str
    source_audio_duration_seconds: float
    source_audio_duration_ms: int
    source_audio_sample_rate: int
    reference_audio_duration_ms: int | None
    output_audio_duration_ms: int | None
    readiness_snapshot: float
    traceability_token: str | None
    profiling_json: dict | None
    error_category: str | None
    error_message: str | None
    processing_started_at: datetime | None
    processing_finished_at: datetime | None
    processing_duration_ms: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
