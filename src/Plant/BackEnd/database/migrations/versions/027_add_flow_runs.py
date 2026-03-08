"""add_flow_runs

Revision ID: 027_add_flow_runs
Revises: 026_campaign_tables
Create Date: 2026-03-08

Stories: EXEC-ENGINE-001 E1-S1 — flow_run table with 6-status machine
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "027_add_flow_runs"
down_revision = "026_campaign_tables"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Create flow_runs table with status machine and idempotency constraint."""

    op.create_table(
        "flow_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hired_instance_id", sa.String(), nullable=False),
        sa.Column("skill_id", sa.String(), nullable=False),
        sa.Column("flow_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("current_step", sa.String(), nullable=True),
        sa.Column(
            "run_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "error_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_flow_runs"),
        sa.UniqueConstraint("idempotency_key", name="uq_flow_runs_idempotency_key"),
    )

    op.create_index("ix_flow_runs_hired_instance_id", "flow_runs", ["hired_instance_id"])
    op.create_index("ix_flow_runs_status", "flow_runs", ["status"])
    op.create_index("ix_flow_runs_idempotency_key", "flow_runs", ["idempotency_key"])


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Drop flow_runs table."""
    op.drop_index("ix_flow_runs_idempotency_key", table_name="flow_runs")
    op.drop_index("ix_flow_runs_status", table_name="flow_runs")
    op.drop_index("ix_flow_runs_hired_instance_id", table_name="flow_runs")
    op.drop_table("flow_runs")
