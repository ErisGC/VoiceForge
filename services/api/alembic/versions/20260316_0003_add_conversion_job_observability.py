"""Add conversion job observability and metric columns."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260316_0003"
down_revision = "20260316_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversion_jobs",
        sa.Column("source_audio_duration_ms", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("conversion_jobs", sa.Column("reference_audio_duration_ms", sa.Integer(), nullable=True))
    op.add_column("conversion_jobs", sa.Column("output_audio_duration_ms", sa.Integer(), nullable=True))
    op.add_column("conversion_jobs", sa.Column("error_category", sa.String(length=64), nullable=True))
    op.add_column("conversion_jobs", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("conversion_jobs", sa.Column("processing_finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("conversion_jobs", sa.Column("processing_duration_ms", sa.Integer(), nullable=True))

    op.execute(
        "UPDATE conversion_jobs "
        "SET source_audio_duration_ms = CAST(source_audio_duration_seconds * 1000 AS INTEGER)"
    )
    op.execute(
        "UPDATE conversion_jobs SET processing_started_at = started_at WHERE started_at IS NOT NULL"
    )
    op.execute(
        "UPDATE conversion_jobs SET processing_finished_at = completed_at WHERE completed_at IS NOT NULL"
    )
    op.alter_column("conversion_jobs", "source_audio_duration_ms", server_default=None)


def downgrade() -> None:
    op.drop_column("conversion_jobs", "processing_duration_ms")
    op.drop_column("conversion_jobs", "processing_finished_at")
    op.drop_column("conversion_jobs", "processing_started_at")
    op.drop_column("conversion_jobs", "error_category")
    op.drop_column("conversion_jobs", "output_audio_duration_ms")
    op.drop_column("conversion_jobs", "reference_audio_duration_ms")
    op.drop_column("conversion_jobs", "source_audio_duration_ms")
