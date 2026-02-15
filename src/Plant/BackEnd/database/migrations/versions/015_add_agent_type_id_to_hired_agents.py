"""add_agent_type_id_to_hired_agents

Revision ID: 015_add_agent_type_id_to_hired_agents
Revises: 014_seed_demo_customer
Create Date: 2026-02-15

Story: PH1-3.1 - DB-backed hired agent instance must preserve agent_type_id
Purpose: Persist Phase-1 catalog-driven agent_type_id on DB-backed hired instances.

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015_add_agent_type_id_to_hired_agents"
down_revision = "014_seed_demo_customer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hired_agents", sa.Column("agent_type_id", sa.String(), nullable=True))
    op.create_index("ix_hired_agents_agent_type_id", "hired_agents", ["agent_type_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_hired_agents_agent_type_id", table_name="hired_agents")
    op.drop_column("hired_agents", "agent_type_id")
