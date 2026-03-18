"""Add conversion job profiling payload."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260316_0004"
down_revision = "20260316_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversion_jobs", sa.Column("profiling_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversion_jobs", "profiling_json")
