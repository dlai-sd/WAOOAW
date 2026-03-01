"""platform_connections table

Revision ID: 022_platform_connections
Revises: 021_agent_skills_and_skill_goal_schema
Create Date: 2026-03-01

PLANT-SKILLS-1 E2-S1

Stores external platform credential references (GCP Secret Manager paths only —
NEVER the actual secret value) linked to a HiredAgent instance and a Skill.

Platform key examples: "delta_exchange", "instagram", "facebook", "x"
"""

from alembic import op
import sqlalchemy as sa

revision = "022_platform_connections"
down_revision = "021_agent_skills_and_skill_goal_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "hired_instance_id",
            sa.String,
            sa.ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String, nullable=False),
        sa.Column("platform_key", sa.String(100), nullable=False),
        # GCP Secret Manager resource path ONLY — never the actual secret value
        # e.g. "projects/waooaw-oauth/secrets/hired-abc123-delta-exchange/versions/latest"
        sa.Column("secret_ref", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),  # pending | connected | error
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_platform_conn_hired_skill_platform",
        "platform_connections",
        ["hired_instance_id", "skill_id", "platform_key"],
    )
    op.create_index(
        "ix_platform_connections_hired_instance_id",
        "platform_connections",
        ["hired_instance_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_connections_hired_instance_id",
        table_name="platform_connections",
    )
    op.drop_constraint(
        "uq_platform_conn_hired_skill_platform",
        "platform_connections",
        type_="unique",
    )
    op.drop_table("platform_connections")
