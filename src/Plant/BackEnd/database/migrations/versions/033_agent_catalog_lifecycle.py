"""add agent catalog lifecycle table and hired-agent snapshot columns

Revision ID: 033_agent_catalog_lifecycle
Revises: 032_seed_demo_dma_runtime
Create Date: 2026-03-13

Stories: PLANT-CATALOG-1 E1-S1 — Plant-owned hire-ready catalog lifecycle
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "033_agent_catalog_lifecycle"
down_revision = "032_seed_demo_dma_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_catalog_releases",
        sa.Column("release_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("agent_type_id", sa.String(), nullable=False),
        sa.Column("internal_definition_version_id", sa.String(), nullable=True),
        sa.Column("external_catalog_version", sa.String(), nullable=False),
        sa.Column("public_name", sa.String(), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("industry_name", sa.String(), nullable=False),
        sa.Column("job_role_label", sa.String(), nullable=False),
        sa.Column("monthly_price_inr", sa.Integer(), nullable=False, server_default="12000"),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("allowed_durations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='["monthly", "quarterly"]'),
        sa.Column("supported_channels", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("approval_mode", sa.String(), nullable=False, server_default="manual_review"),
        sa.Column("lifecycle_state", sa.String(), nullable=False, server_default="draft"),
        sa.Column("approved_for_new_hire", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retired_from_catalog_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("release_id", name="pk_agent_catalog_releases"),
        sa.UniqueConstraint("agent_id", "external_catalog_version", name="uq_agent_catalog_agent_version"),
    )

    op.create_index("ix_agent_catalog_releases_agent_id", "agent_catalog_releases", ["agent_id"])
    op.create_index("ix_agent_catalog_releases_lifecycle_state", "agent_catalog_releases", ["lifecycle_state"])
    op.create_index("ix_agent_catalog_releases_approved_for_new_hire", "agent_catalog_releases", ["approved_for_new_hire"])

    op.add_column("hired_agents", sa.Column("catalog_release_id", sa.String(), nullable=True))
    op.add_column("hired_agents", sa.Column("internal_definition_version_id", sa.String(), nullable=True))
    op.add_column("hired_agents", sa.Column("external_catalog_version", sa.String(), nullable=True))
    op.add_column("hired_agents", sa.Column("catalog_status_at_hire", sa.String(), nullable=True))
    op.create_index("ix_hired_agents_catalog_release_id", "hired_agents", ["catalog_release_id"])


def downgrade() -> None:
    op.drop_index("ix_hired_agents_catalog_release_id", table_name="hired_agents")
    op.drop_column("hired_agents", "catalog_status_at_hire")
    op.drop_column("hired_agents", "external_catalog_version")
    op.drop_column("hired_agents", "internal_definition_version_id")
    op.drop_column("hired_agents", "catalog_release_id")

    op.drop_index("ix_agent_catalog_releases_approved_for_new_hire", table_name="agent_catalog_releases")
    op.drop_index("ix_agent_catalog_releases_lifecycle_state", table_name="agent_catalog_releases")
    op.drop_index("ix_agent_catalog_releases_agent_id", table_name="agent_catalog_releases")
    op.drop_table("agent_catalog_releases")