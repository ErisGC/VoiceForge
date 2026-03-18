from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.orm import Session

from voiceforge_core.db.models import SpeakerEmbedding
from voiceforge_core.inference.contracts import SpeakerEmbeddingService
from voiceforge_core.storage.base import StorageProvider


class SpeakerEmbeddingPersistenceService:
    @staticmethod
    def create_embedding(
        session: Session,
        *,
        storage: StorageProvider,
        extractor: SpeakerEmbeddingService,
        voice_profile_id: UUID,
        voice_sample_id: UUID,
        audio_bytes: bytes,
        sample_rate: int,
    ) -> SpeakerEmbedding:
        artifact = extractor.extract(audio_bytes=audio_bytes, sample_rate=sample_rate)
        key = f"embeddings/{voice_profile_id}/{voice_sample_id}.json"
        storage.put_bytes(
            key=key,
            payload=json.dumps(
                {
                    "vector": artifact.vector,
                    "metadata": artifact.metadata,
                    "checksum": artifact.checksum,
                },
                indent=2,
            ).encode("utf-8"),
            content_type="application/json",
        )
        embedding = SpeakerEmbedding(
            voice_profile_id=voice_profile_id,
            voice_sample_id=voice_sample_id,
            backend_name=artifact.backend_name,
            embedding_version=artifact.embedding_version,
            dimension=artifact.dimension,
            vector_storage_key=key,
            checksum=artifact.checksum,
            metadata_json=artifact.metadata,
        )
        session.add(embedding)
        session.flush()
        return embedding

