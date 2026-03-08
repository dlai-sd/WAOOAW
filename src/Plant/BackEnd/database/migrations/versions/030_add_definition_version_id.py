"""add_definition_version_id_to_hired_agents

Revision ID: 030_add_definition_version_id
Revises: 029_add_skill_configs
Create Date: 2026-03-08

Stories: EXEC-ENGINE-001 E2-S1 — pin hired agent to definition version at hire time
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "030_add_definition_version_id"
down_revision = "029_add_skill_configs"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Add nullable definition_version_id column to hired_agents."""
    op.add_column(
        "hired_agents",
        sa.Column("definition_version_id", sa.String(), nullable=True),
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Remove definition_version_id column from hired_agents."""
    op.drop_column("hired_agents", "definition_version_id")
