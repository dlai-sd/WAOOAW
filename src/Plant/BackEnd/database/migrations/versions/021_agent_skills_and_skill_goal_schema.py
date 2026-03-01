"""agent_skills join table + goal_schema on skill_entity

Revision ID: 021_agent_skills_and_skill_goal_schema
Revises: 020_pii_encryption
Create Date: 2026-03-01

PLANT-SKILLS-1 E1-S1

Changes:
1. Add goal_schema JSONB column to skill_entity (nullable — existing rows get NULL)
2. Create agent_skills join table (agent ↔ skill many-to-many)
3. Make agent_entity.skill_id nullable (backward compat — NOT dropped)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "021_agent_skills_and_skill_goal_schema"
down_revision = "020_pii_encryption"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add goal_schema JSONB to skill_entity (nullable — existing rows get NULL)
    op.add_column(
        "skill_entity",
        sa.Column("goal_schema", postgresql.JSONB, nullable=True),
    )

    # 2. Create agent_skills join table
    op.create_table(
        "agent_skills",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_agent_skills_agent_skill", "agent_skills", ["agent_id", "skill_id"]
    )
    op.create_index("ix_agent_skills_agent_id", "agent_skills", ["agent_id"])
    op.create_index("ix_agent_skills_skill_id", "agent_skills", ["skill_id"])

    # 3. Make agent_entity.skill_id nullable (backward compat — do NOT drop it)
    op.alter_column("agent_entity", "skill_id", nullable=True)


def downgrade() -> None:
    op.drop_index("ix_agent_skills_skill_id", table_name="agent_skills")
    op.drop_index("ix_agent_skills_agent_id", table_name="agent_skills")
    op.drop_constraint("uq_agent_skills_agent_skill", "agent_skills", type_="unique")
    op.drop_table("agent_skills")
    op.drop_column("skill_entity", "goal_schema")
    op.alter_column("agent_entity", "skill_id", nullable=False)
