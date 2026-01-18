"""
Create skill_entity table

Revision ID: 002_skill_entity
Revises: 001_base_entity
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '002_skill_entity'
down_revision = '001_base_entity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create skill_entity table (inherits from base_entity structure).
    """
    
    op.create_table(
        'skill_entity',
        # INHERIT ALL COLUMNS FROM BASE_ENTITY (copy structure)
        sa.Column('id', UUID(as_uuid=True), sa.ForeignKey('base_entity.id', ondelete='CASCADE'), primary_key=True),
        
        # SKILL-SPECIFIC COLUMNS
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('embedding_384', sa.Text, nullable=True),  # Will use vector type after pgvector migration
    )
    
    # Create indexes
    op.create_index('ix_skill_name', 'skill_entity', ['name'])
    op.create_index('ix_skill_category', 'skill_entity', ['category'])


def downgrade() -> None:
    """
    Drop skill_entity table.
    """
    op.drop_index('ix_skill_category', 'skill_entity')
    op.drop_index('ix_skill_name', 'skill_entity')
    op.drop_table('skill_entity')
