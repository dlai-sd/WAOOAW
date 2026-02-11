"""create_agent_type_definitions_table

Revision ID: ce2ce3126c3b
Revises: 009_customer_unique_phone
Create Date: 2026-02-11 09:22:32.917341

Story: AGP1-DB-1.1 - Create AgentTypeDefinition DB model + migration
Purpose: Persist agent type schemas and goal templates in DB (move from in-memory)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'ce2ce3126c3b'
down_revision = '009_customer_unique_phone'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agent_type_definitions table with JSONB payload column."""
    
    op.create_table(
        'agent_type_definitions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_type_id', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_agent_type_definitions'),
        sa.UniqueConstraint('agent_type_id', 'version', name='uq_agent_type_id_version')
    )
    
    # Create index for faster lookups by agent_type_id
    op.create_index(
        'ix_agent_type_definitions_agent_type_id',
        'agent_type_definitions',
        ['agent_type_id'],
        unique=False
    )


def downgrade() -> None:
    """Drop agent_type_definitions table and associated indexes."""
    
    op.drop_index('ix_agent_type_definitions_agent_type_id', table_name='agent_type_definitions')
    op.drop_table('agent_type_definitions')
