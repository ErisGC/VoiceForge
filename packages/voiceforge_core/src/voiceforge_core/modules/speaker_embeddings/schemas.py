from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SpeakerEmbeddingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    voice_profile_id: UUID
    voice_sample_id: UUID | None
    backend_name: str
    embedding_version: str
    dimension: int
    vector_storage_key: str
    checksum: str
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime

