"""add_component_runs

Revision ID: 028_add_component_runs
Revises: 027_add_flow_runs
Create Date: 2026-03-08

Stories: EXEC-ENGINE-001 E1-S2 — component_run table with FK to flow_runs
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "028_add_component_runs"
down_revision = "027_add_flow_runs"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Create component_runs table with FK to flow_runs."""

    op.create_table(
        "component_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("flow_run_id", sa.String(), nullable=False),
        sa.Column("component_type", sa.String(), nullable=False),
        sa.Column("step_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column(
            "input_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "output",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_component_runs"),
        sa.ForeignKeyConstraint(
            ["flow_run_id"],
            ["flow_runs.id"],
            name="fk_component_runs_flow_run",
            ondelete="CASCADE",
        ),
    )

    op.create_index("ix_component_runs_flow_run_id", "component_runs", ["flow_run_id"])
    op.create_index("ix_component_runs_component_type", "component_runs", ["component_type"])
    op.create_index("ix_component_runs_status", "component_runs", ["status"])


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Drop component_runs table."""
    op.drop_index("ix_component_runs_status", table_name="component_runs")
    op.drop_index("ix_component_runs_component_type", table_name="component_runs")
    op.drop_index("ix_component_runs_flow_run_id", table_name="component_runs")
    op.drop_table("component_runs")
