"""Initial VoiceForge schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260316_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("user", "admin", name="user_role")
    engine_backend = sa.Enum("seed_vc", "rvc", "openvoice", name="engine_backend")
    voice_profile_status = sa.Enum(
        "draft", "ready", "training", "active", "archived", name="voice_profile_status"
    )
    voice_sample_source = sa.Enum("upload", "microphone", "import", name="voice_sample_source")
    processing_status = sa.Enum("pending", "ready", "failed", name="voice_sample_processing_status")
    job_status_training = sa.Enum(
        "pending", "queued", "running", "completed", "failed", "cancelled", name="training_job_status"
    )
    job_status_conversion = sa.Enum(
        "pending", "queued", "running", "completed", "failed", "cancelled", name="conversion_job_status"
    )
    conversion_mode = sa.Enum("studio", "live", name="conversion_mode")
    training_backend = sa.Enum("seed_vc", "rvc", "openvoice", name="training_engine_backend")
    conversion_backend = sa.Enum("seed_vc", "rvc", "openvoice", name="conversion_engine_backend")
    audit_event_type = sa.Enum(
        "auth_register",
        "auth_login",
        "voice_profile_created",
        "voice_sample_uploaded",
        "training_job_created",
        "training_job_started",
        "training_job_completed",
        "training_job_failed",
        "conversion_job_created",
        "conversion_job_started",
        "conversion_job_completed",
        "conversion_job_failed",
        name="audit_event_type",
    )

    bind = op.get_bind()
    for enum in (
        user_role,
        engine_backend,
        voice_profile_status,
        voice_sample_source,
        processing_status,
        job_status_training,
        job_status_conversion,
        conversion_mode,
        training_backend,
        conversion_backend,
        audit_event_type,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "voice_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preferred_backend", engine_backend, nullable=False),
        sa.Column("status", voice_profile_status, nullable=False),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column("consent_captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_evidence_storage_key", sa.String(length=512), nullable=True),
        sa.Column("watermark_template", sa.JSON(), nullable=True),
        sa.Column("total_duration_seconds", sa.Float(), nullable=False),
        sa.Column("clip_count", sa.Integer(), nullable=False),
        sa.Column("noise_score", sa.Float(), nullable=False),
        sa.Column("diversity_score", sa.Float(), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_voice_profiles_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_voice_profiles"),
    )
    op.create_index("ix_voice_profiles_user_id", "voice_profiles", ["user_id"], unique=False)
    op.create_index(
        "ix_voice_profiles_user_status",
        "voice_profiles",
        ["user_id", "status"],
        unique=False,
    )

    op.create_table(
        "voice_samples",
        sa.Column("voice_profile_id", sa.Uuid(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
        sa.Column("source", voice_sample_source, nullable=False),
        sa.Column("processing_status", processing_status, nullable=False),
        sa.Column("noise_score", sa.Float(), nullable=False),
        sa.Column("diversity_score", sa.Float(), nullable=False),
        sa.Column("vad_segments", sa.JSON(), nullable=True),
        sa.Column("waveform_hash", sa.String(length=128), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"], name="fk_voice_samples_voice_profile_id_voice_profiles"),
        sa.PrimaryKeyConstraint("id", name="pk_voice_samples"),
        sa.UniqueConstraint("storage_key", name="uq_voice_samples_storage_key"),
    )
    op.create_index("ix_voice_samples_voice_profile_id", "voice_samples", ["voice_profile_id"], unique=False)

    op.create_table(
        "speaker_embeddings",
        sa.Column("voice_profile_id", sa.Uuid(), nullable=False),
        sa.Column("voice_sample_id", sa.Uuid(), nullable=True),
        sa.Column("backend_name", sa.String(length=255), nullable=False),
        sa.Column("embedding_version", sa.String(length=64), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("vector_storage_key", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"], name="fk_speaker_embeddings_voice_profile_id_voice_profiles"),
        sa.ForeignKeyConstraint(["voice_sample_id"], ["voice_samples.id"], name="fk_speaker_embeddings_voice_sample_id_voice_samples"),
        sa.PrimaryKeyConstraint("id", name="pk_speaker_embeddings"),
    )
    op.create_index("ix_speaker_embeddings_voice_profile_id", "speaker_embeddings", ["voice_profile_id"], unique=False)
    op.create_index("ix_speaker_embeddings_voice_sample_id", "speaker_embeddings", ["voice_sample_id"], unique=False)

    op.create_table(
        "training_jobs",
        sa.Column("voice_profile_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("backend", training_backend, nullable=False),
        sa.Column("status", job_status_training, nullable=False),
        sa.Column("queue_name", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("model_artifact_storage_key", sa.String(length=512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], name="fk_training_jobs_requested_by_user_id_users"),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"], name="fk_training_jobs_voice_profile_id_voice_profiles"),
        sa.PrimaryKeyConstraint("id", name="pk_training_jobs"),
    )
    op.create_index("ix_training_jobs_requested_by_user_id", "training_jobs", ["requested_by_user_id"], unique=False)
    op.create_index("ix_training_jobs_voice_profile_id", "training_jobs", ["voice_profile_id"], unique=False)

    op.create_table(
        "conversion_jobs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("voice_profile_id", sa.Uuid(), nullable=False),
        sa.Column("backend", conversion_backend, nullable=False),
        sa.Column("mode", conversion_mode, nullable=False),
        sa.Column("status", job_status_conversion, nullable=False),
        sa.Column("queue_name", sa.String(length=255), nullable=False),
        sa.Column("source_audio_bucket", sa.String(length=255), nullable=False),
        sa.Column("source_audio_storage_key", sa.String(length=512), nullable=False),
        sa.Column("source_audio_filename", sa.String(length=255), nullable=False),
        sa.Column("source_audio_content_type", sa.String(length=255), nullable=False),
        sa.Column("source_audio_duration_seconds", sa.Float(), nullable=False),
        sa.Column("source_audio_sample_rate", sa.Integer(), nullable=False),
        sa.Column("readiness_snapshot", sa.Float(), nullable=False),
        sa.Column("traceability_token", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_conversion_jobs_user_id_users"),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"], name="fk_conversion_jobs_voice_profile_id_voice_profiles"),
        sa.PrimaryKeyConstraint("id", name="pk_conversion_jobs"),
        sa.UniqueConstraint("source_audio_storage_key", name="uq_conversion_jobs_source_audio_storage_key"),
    )
    op.create_index("ix_conversion_jobs_user_id", "conversion_jobs", ["user_id"], unique=False)
    op.create_index("ix_conversion_jobs_voice_profile_id", "conversion_jobs", ["voice_profile_id"], unique=False)

    op.create_table(
        "converted_audios",
        sa.Column("conversion_job_id", sa.Uuid(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("watermark_status", sa.String(length=64), nullable=False),
        sa.Column("traceability_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversion_job_id"], ["conversion_jobs.id"], name="fk_converted_audios_conversion_job_id_conversion_jobs"),
        sa.PrimaryKeyConstraint("id", name="pk_converted_audios"),
        sa.UniqueConstraint("storage_key", name="uq_converted_audios_storage_key"),
    )
    op.create_index("ix_converted_audios_conversion_job_id", "converted_audios", ["conversion_job_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_audit_logs_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False)
    op.create_index(
        "ix_audit_logs_entity_created",
        "audit_logs",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_converted_audios_conversion_job_id", table_name="converted_audios")
    op.drop_table("converted_audios")

    op.drop_index("ix_conversion_jobs_voice_profile_id", table_name="conversion_jobs")
    op.drop_index("ix_conversion_jobs_user_id", table_name="conversion_jobs")
    op.drop_table("conversion_jobs")

    op.drop_index("ix_training_jobs_voice_profile_id", table_name="training_jobs")
    op.drop_index("ix_training_jobs_requested_by_user_id", table_name="training_jobs")
    op.drop_table("training_jobs")

    op.drop_index("ix_speaker_embeddings_voice_sample_id", table_name="speaker_embeddings")
    op.drop_index("ix_speaker_embeddings_voice_profile_id", table_name="speaker_embeddings")
    op.drop_table("speaker_embeddings")

    op.drop_index("ix_voice_samples_voice_profile_id", table_name="voice_samples")
    op.drop_table("voice_samples")

    op.drop_index("ix_voice_profiles_user_status", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_user_id", table_name="voice_profiles")
    op.drop_table("voice_profiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

