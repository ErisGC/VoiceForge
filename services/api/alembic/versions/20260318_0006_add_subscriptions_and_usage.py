"""Add subscriptions and usage counters."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260318_0006"
down_revision = "20260316_0005"
branch_labels = None
depends_on = None


subscription_plan = sa.Enum("free", "pro", "unlimited", name="subscription_plan")
subscription_status = sa.Enum("active", "cancelled", "expired", "past_due", name="subscription_status")


def upgrade() -> None:
    subscription_plan.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("plan", subscription_plan, nullable=False, server_default="free"),
        sa.Column("status", subscription_status, nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wompi_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("payment_reference", sa.String(length=512), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_status", "subscriptions", ["user_id", "status"], unique=False)
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=False)

    op.create_table(
        "usage_counters",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("period_month", sa.String(length=7), nullable=False),
        sa.Column("conversions_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_usage_counters_user_period", "usage_counters", ["user_id", "period_month"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_usage_counters_user_period", table_name="usage_counters")
    op.drop_table("usage_counters")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_status", table_name="subscriptions")
    op.drop_table("subscriptions")
    subscription_status.drop(op.get_bind(), checkfirst=True)
    subscription_plan.drop(op.get_bind(), checkfirst=True)
