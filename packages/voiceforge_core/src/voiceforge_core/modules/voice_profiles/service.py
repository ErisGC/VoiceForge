from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from voiceforge_core.audio.pipeline import compute_dataset_quality
from voiceforge_core.db.enums import VoiceProfileStatus
from voiceforge_core.db.models import User, VoiceProfile, VoiceSample
from voiceforge_core.modules.voice_profiles.schemas import VoiceProfileCreate


class VoiceProfileService:
    @staticmethod
    def create_profile(session: Session, user: User, payload: VoiceProfileCreate) -> VoiceProfile:
        if not payload.consent_confirmed:
            raise ValueError("Consent is required before creating a voice profile.")
        profile = VoiceProfile(
            user_id=user.id,
            name=payload.name.strip(),
            description=payload.description,
            preferred_backend=payload.preferred_backend,
            consent_confirmed=payload.consent_confirmed,
            consent_text=payload.consent_text,
            consent_captured_at=datetime.now(timezone.utc),
            consent_evidence_storage_key=payload.consent_evidence_storage_key,
            status=VoiceProfileStatus.DRAFT,
            watermark_template={"strategy": "voiceforge-trace-v1", "enabled": False},
        )
        session.add(profile)
        session.flush()
        return profile

    @staticmethod
    def list_for_user(session: Session, user_id: UUID) -> list[VoiceProfile]:
        statement = (
            select(VoiceProfile)
            .where(VoiceProfile.user_id == user_id)
            .order_by(VoiceProfile.created_at.desc())
        )
        return list(session.scalars(statement))

    @staticmethod
    def get_for_user(session: Session, user_id: UUID, profile_id: UUID) -> VoiceProfile | None:
        statement = (
            select(VoiceProfile)
            .where(VoiceProfile.user_id == user_id, VoiceProfile.id == profile_id)
            .options(
                selectinload(VoiceProfile.voice_samples),
                selectinload(VoiceProfile.speaker_embeddings),
                selectinload(VoiceProfile.training_jobs),
            )
        )
        return session.scalar(statement)

    @staticmethod
    def refresh_metrics(session: Session, profile: VoiceProfile) -> VoiceProfile:
        samples = list(
            session.scalars(
                select(VoiceSample).where(VoiceSample.voice_profile_id == profile.id).order_by(VoiceSample.created_at)
            )
        )
        if not samples:
            profile.total_duration_seconds = 0.0
            profile.clip_count = 0
            profile.noise_score = 1.0
            profile.diversity_score = 0.0
            profile.sample_rate = 0
            profile.readiness_score = 0.0
            profile.status = VoiceProfileStatus.DRAFT
            session.flush()
            return profile

        metrics = compute_dataset_quality(
            durations=[sample.duration_seconds for sample in samples],
            noise_scores=[sample.noise_score for sample in samples],
            sample_rates=[sample.sample_rate for sample in samples if sample.sample_rate > 0],
        )
        profile.total_duration_seconds = metrics.total_duration_seconds
        profile.clip_count = metrics.clip_count
        profile.noise_score = metrics.noise_score
        profile.diversity_score = metrics.diversity_score
        profile.sample_rate = metrics.sample_rate
        profile.readiness_score = metrics.readiness_score()

        if profile.readiness_score >= 80:
            profile.status = VoiceProfileStatus.READY
        elif profile.clip_count >= 1:
            profile.status = VoiceProfileStatus.DRAFT

        session.flush()
        return profile
