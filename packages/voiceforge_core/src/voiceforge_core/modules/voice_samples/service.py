from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from voiceforge_core.audio.contracts import AudioPreprocessor
from voiceforge_core.db.enums import ProcessingStatus, VoiceSampleSource
from voiceforge_core.db.models import VoiceProfile, VoiceSample
from voiceforge_core.inference.contracts import SpeakerEmbeddingService
from voiceforge_core.modules.feature_caches.service import VoiceProfileFeatureCacheService
from voiceforge_core.modules.speaker_embeddings.service import SpeakerEmbeddingPersistenceService
from voiceforge_core.modules.storage.service import (
    DEFAULT_AUDIO_CONTENT_TYPE,
    validate_audio_filename,
)
from voiceforge_core.modules.voice_profiles.service import VoiceProfileService
from voiceforge_core.storage.base import StorageProvider


class VoiceSampleService:
    @staticmethod
    def list_for_profile(session: Session, profile_id: UUID) -> list[VoiceSample]:
        return list(
            session.scalars(
                select(VoiceSample)
                .where(VoiceSample.voice_profile_id == profile_id)
                .order_by(VoiceSample.created_at.desc())
            )
        )

    @staticmethod
    def create_sample(
        session: Session,
        *,
        storage: StorageProvider,
        preprocessor: AudioPreprocessor,
        embedding_extractor: SpeakerEmbeddingService,
        profile: VoiceProfile,
        original_filename: str,
        content_type: str | None,
        payload: bytes,
        source: VoiceSampleSource,
    ) -> VoiceSample:
        suffix = validate_audio_filename(original_filename)
        key = (
            f"samples/{profile.user_id}/{profile.id}/"
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid4().hex}{suffix}"
        )
        stored = storage.put_bytes(key=key, payload=payload, content_type=content_type or DEFAULT_AUDIO_CONTENT_TYPE)
        report = preprocessor.process(file_path=str(stored.path), size_bytes=stored.size_bytes)

        sample = VoiceSample(
            voice_profile_id=profile.id,
            storage_bucket=stored.bucket,
            storage_key=stored.key,
            original_filename=original_filename,
            content_type=content_type or DEFAULT_AUDIO_CONTENT_TYPE,
            size_bytes=stored.size_bytes,
            duration_seconds=report.metadata.duration_seconds,
            sample_rate=report.metadata.sample_rate,
            channels=report.metadata.channels,
            source=source,
            processing_status=ProcessingStatus.READY,
            noise_score=report.noise_score,
            diversity_score=report.diversity_score,
            vad_segments=[
                {
                    "start_seconds": segment.start_seconds,
                    "end_seconds": segment.end_seconds,
                }
                for segment in report.vad_segments
            ],
            waveform_hash=hashlib.sha256(payload).hexdigest(),
        )
        session.add(sample)
        session.flush()

        SpeakerEmbeddingPersistenceService.create_embedding(
            session,
            storage=storage,
            extractor=embedding_extractor,
            voice_profile_id=profile.id,
            voice_sample_id=sample.id,
            audio_bytes=payload,
            sample_rate=report.metadata.sample_rate,
        )
        VoiceProfileFeatureCacheService.invalidate_active_caches(
            session,
            voice_profile_id=profile.id,
            reason="voice_samples_changed",
        )
        VoiceProfileService.refresh_metrics(session, profile)
        session.flush()
        return sample
