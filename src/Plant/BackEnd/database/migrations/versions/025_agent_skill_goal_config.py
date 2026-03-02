"""Add goal_config JSONB to agent_skills

Revision ID: 025_agent_skill_goal_config
Revises: 024_seed_demo_hired_agents
Create Date: 2026-03-02

Purpose:
    Adds a JSONB `goal_config` column to `agent_skills` (the join table).
    This column stores the customer's per-instance configuration for a skill's
    goal (e.g., target audience, keywords, posting frequency).

    The column is nullable so existing rows are unaffected.  ADD COLUMN IF NOT
    EXISTS makes the migration safe to re-run.

DDL (applied by this migration):
    ALTER TABLE agent_skills
        ADD COLUMN IF NOT EXISTS goal_config JSONB DEFAULT NULL;

Rollback DDL:
    ALTER TABLE agent_skills DROP COLUMN IF EXISTS goal_config;
"""

from __future__ import annotations

from alembic import op


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "025_agent_skill_goal_config"
down_revision = "024_seed_demo_hired_agents"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Add goal_config JSONB column to agent_skills — idempotent."""
    op.execute(
        "ALTER TABLE agent_skills ADD COLUMN IF NOT EXISTS goal_config JSONB DEFAULT NULL"
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Remove goal_config column from agent_skills."""
    op.execute(
        "ALTER TABLE agent_skills DROP COLUMN IF EXISTS goal_config"
    )
