from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from voiceforge_core.db.enums import EngineBackend, JobStatus


class TrainingJobCreate(BaseModel):
    voice_profile_id: UUID
    backend: EngineBackend | None = None


class TrainingJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    voice_profile_id: UUID
    requested_by_user_id: UUID
    backend: EngineBackend
    status: JobStatus
    queue_name: str
    priority: int
    metrics_json: dict | None
    model_artifact_storage_key: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

