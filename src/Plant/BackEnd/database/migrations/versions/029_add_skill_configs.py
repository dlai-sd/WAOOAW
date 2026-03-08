"""add_skill_configs

Revision ID: 029_add_skill_configs
Revises: 028_add_component_runs
Create Date: 2026-03-08

Stories: EXEC-ENGINE-001 E1-S3 — skill_config table with (hired_instance_id, skill_id) unique constraint
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "029_add_skill_configs"
down_revision = "028_add_component_runs"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Create skill_configs table."""

    op.create_table(
        "skill_configs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hired_instance_id", sa.String(), nullable=False),
        sa.Column("skill_id", sa.String(), nullable=False),
        sa.Column("definition_version_id", sa.String(), nullable=False),
        sa.Column(
            "pp_locked_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "customer_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_skill_configs"),
        sa.UniqueConstraint(
            "hired_instance_id", "skill_id", name="uq_skill_config_per_hire"
        ),
    )

    op.create_index(
        "ix_skill_configs_hired_instance_id", "skill_configs", ["hired_instance_id"]
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Drop skill_configs table."""
    op.drop_index("ix_skill_configs_hired_instance_id", table_name="skill_configs")
    op.drop_table("skill_configs")
