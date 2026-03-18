"""Add voice profile feature caches."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260316_0005"
down_revision = "20260316_0004"
branch_labels = None
depends_on = None


feature_cache_engine_backend = sa.Enum(
    "seed_vc",
    "rvc",
    "openvoice",
    name="feature_cache_engine_backend",
)


def upgrade() -> None:
    feature_cache_engine_backend.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "voice_profile_feature_caches",
        sa.Column("voice_profile_id", sa.Uuid(), nullable=False),
        sa.Column("backend", feature_cache_engine_backend, nullable=False),
        sa.Column("cache_namespace", sa.String(length=128), nullable=False),
        sa.Column("artifact_version", sa.String(length=64), nullable=False),
        sa.Column("cache_format", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sample_signature", sa.String(length=128), nullable=False),
        sa.Column("config_signature", sa.String(length=128), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False, server_default="application/octet-stream"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("invalidation_reason", sa.String(length=128), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_voice_profile_feature_cache_lookup",
        "voice_profile_feature_caches",
        ["voice_profile_id", "backend", "cache_namespace", "invalidated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_profile_feature_caches_voice_profile_id"),
        "voice_profile_feature_caches",
        ["voice_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_voice_profile_feature_caches_voice_profile_id"), table_name="voice_profile_feature_caches")
    op.drop_index("ix_voice_profile_feature_cache_lookup", table_name="voice_profile_feature_caches")
    op.drop_table("voice_profile_feature_caches")
    feature_cache_engine_backend.drop(op.get_bind(), checkfirst=True)
