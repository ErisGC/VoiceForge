from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from voiceforge_core.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from voiceforge_core.db.enums import (
    AuditEventType,
    ConversionMode,
    EngineBackend,
    JobStatus,
    ProcessingStatus,
    SubscriptionPlan,
    SubscriptionStatus,
    UserRole,
    VoiceProfileStatus,
    VoiceSampleSource,
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    voice_profiles: Mapped[list["VoiceProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[list["TrainingJob"]] = relationship(back_populates="requested_by")
    conversion_jobs: Mapped[list["ConversionJob"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class VoiceProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voice_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_backend: Mapped[EngineBackend] = mapped_column(
        Enum(EngineBackend, name="engine_backend"),
        nullable=False,
        default=EngineBackend.SEED_VC,
    )
    status: Mapped[VoiceProfileStatus] = mapped_column(
        Enum(VoiceProfileStatus, name="voice_profile_status"),
        nullable=False,
        default=VoiceProfileStatus.DRAFT,
    )
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    consent_captured_at: Mapped[datetime | None] = mapped_column(nullable=True)
    consent_evidence_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    watermark_template: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    clip_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    noise_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    diversity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    user: Mapped["User"] = relationship(back_populates="voice_profiles")
    voice_samples: Mapped[list["VoiceSample"]] = relationship(
        back_populates="voice_profile", cascade="all, delete-orphan"
    )
    speaker_embeddings: Mapped[list["SpeakerEmbedding"]] = relationship(
        back_populates="voice_profile", cascade="all, delete-orphan"
    )
    feature_caches: Mapped[list["VoiceProfileFeatureCache"]] = relationship(
        back_populates="voice_profile", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[list["TrainingJob"]] = relationship(
        back_populates="voice_profile", cascade="all, delete-orphan"
    )
    conversion_jobs: Mapped[list["ConversionJob"]] = relationship(back_populates="voice_profile")

    __table_args__ = (Index("ix_voice_profiles_user_status", "user_id", "status"),)


class VoiceSample(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voice_samples"

    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id"), nullable=False, index=True
    )
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channels: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source: Mapped[VoiceSampleSource] = mapped_column(
        Enum(VoiceSampleSource, name="voice_sample_source"),
        nullable=False,
        default=VoiceSampleSource.UPLOAD,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="voice_sample_processing_status"),
        nullable=False,
        default=ProcessingStatus.READY,
    )
    noise_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    diversity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    vad_segments: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    waveform_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    voice_profile: Mapped["VoiceProfile"] = relationship(back_populates="voice_samples")
    speaker_embeddings: Mapped[list["SpeakerEmbedding"]] = relationship(
        back_populates="voice_sample", cascade="all, delete-orphan"
    )


class SpeakerEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "speaker_embeddings"

    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id"), nullable=False, index=True
    )
    voice_sample_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("voice_samples.id"), nullable=True, index=True
    )
    backend_name: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(64), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    voice_profile: Mapped["VoiceProfile"] = relationship(back_populates="speaker_embeddings")
    voice_sample: Mapped[VoiceSample | None] = relationship(back_populates="speaker_embeddings")


class VoiceProfileFeatureCache(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voice_profile_feature_caches"

    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id"), nullable=False, index=True
    )
    backend: Mapped[EngineBackend] = mapped_column(
        Enum(EngineBackend, name="feature_cache_engine_backend"),
        nullable=False,
        default=EngineBackend.SEED_VC,
    )
    cache_namespace: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_version: Mapped[str] = mapped_column(String(64), nullable=False)
    cache_format: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sample_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    config_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False, default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    voice_profile: Mapped["VoiceProfile"] = relationship(back_populates="feature_caches")

    __table_args__ = (
        Index(
            "ix_voice_profile_feature_cache_lookup",
            "voice_profile_id",
            "backend",
            "cache_namespace",
            "invalidated_at",
        ),
    )


class TrainingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "training_jobs"

    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    backend: Mapped[EngineBackend] = mapped_column(
        Enum(EngineBackend, name="training_engine_backend"),
        nullable=False,
        default=EngineBackend.SEED_VC,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="training_job_status"), nullable=False, default=JobStatus.PENDING
    )
    queue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_artifact_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    voice_profile: Mapped["VoiceProfile"] = relationship(back_populates="training_jobs")
    requested_by: Mapped["User"] = relationship(back_populates="training_jobs")


class ConversionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversion_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    voice_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id"), nullable=False, index=True
    )
    backend: Mapped[EngineBackend] = mapped_column(
        Enum(EngineBackend, name="conversion_engine_backend"),
        nullable=False,
        default=EngineBackend.SEED_VC,
    )
    mode: Mapped[ConversionMode] = mapped_column(
        Enum(ConversionMode, name="conversion_mode"),
        nullable=False,
        default=ConversionMode.STUDIO,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="conversion_job_status"), nullable=False, default=JobStatus.PENDING
    )
    queue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_audio_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    source_audio_storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    source_audio_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_audio_content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    source_audio_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_audio_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_audio_sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_audio_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_audio_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    readiness_snapshot: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traceability_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profiling_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="conversion_jobs")
    voice_profile: Mapped["VoiceProfile"] = relationship(back_populates="conversion_jobs")
    converted_audios: Mapped[list["ConvertedAudio"]] = relationship(
        back_populates="conversion_job", cascade="all, delete-orphan"
    )


class ConvertedAudio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "converted_audios"

    conversion_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversion_jobs.id"), nullable=False, index=True
    )
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watermark_status: Mapped[str] = mapped_column(String(64), nullable=False, default="reserved")
    traceability_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    conversion_job: Mapped["ConversionJob"] = relationship(back_populates="converted_audios")


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan"),
        nullable=False,
        default=SubscriptionPlan.FREE,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_start: Mapped[datetime] = mapped_column(nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(nullable=False)
    wompi_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    grace_period_end: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(backref="subscriptions")

    __table_args__ = (Index("ix_subscriptions_user_status", "user_id", "status"),)


class UsageCounter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usage_counters"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    period_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    conversions_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(backref="usage_counters")

    __table_args__ = (
        Index("uq_usage_counters_user_period", "user_id", "period_month", unique=True),
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    user: Mapped[User | None] = relationship(back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),)
