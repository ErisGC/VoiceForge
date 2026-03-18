"""Add processing state to job enums."""

from __future__ import annotations

from alembic import op

revision = "20260316_0002"
down_revision = "20260316_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE conversion_job_status ADD VALUE IF NOT EXISTS 'processing'")
    op.execute("ALTER TYPE training_job_status ADD VALUE IF NOT EXISTS 'processing'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely in-place.
    pass
