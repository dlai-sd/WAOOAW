"""
Create job_role, team, agent, industry entities

Revision ID: 003_remaining_entities
Revises: 002_skill_entity
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# revision identifiers
revision = '003_remaining_entities'
down_revision = '002_skill_entity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create job_role, team, agent, industry tables.
    """
    
    # JobRole Entity
    op.create_table(
        'job_role_entity',
        sa.Column('id', UUID(as_uuid=True), sa.ForeignKey('base_entity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('required_skills', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('seniority_level', sa.String(20), nullable=False, server_default='mid'),
        sa.Column('industry_id', UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_job_role_name', 'job_role_entity', ['name'])
    op.create_index('ix_job_role_seniority_level', 'job_role_entity', ['seniority_level'])
    
    # Team Entity
    op.create_table(
        'team_entity',
        sa.Column('id', UUID(as_uuid=True), sa.ForeignKey('base_entity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('agents', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('job_role_id', UUID(as_uuid=True), nullable=False),
        sa.Column('industry_id', UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_team_name', 'team_entity', ['name'])
    op.create_index('ix_team_job_role_id', 'team_entity', ['job_role_id'])
    
    # Agent Entity
    op.create_table(
        'agent_entity',
        sa.Column('id', UUID(as_uuid=True), sa.ForeignKey('base_entity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('skill_id', UUID(as_uuid=True), nullable=False),
        sa.Column('job_role_id', UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', UUID(as_uuid=True), nullable=True),
        sa.Column('industry_id', UUID(as_uuid=True), nullable=False),
    )
    op.create_index('ix_agent_name', 'agent_entity', ['name'])
    op.create_index('ix_agent_industry_id', 'agent_entity', ['industry_id'])
    
    # Industry Entity
    op.create_table(
        'industry_entity',
        sa.Column('id', UUID(as_uuid=True), sa.ForeignKey('base_entity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('agents', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('embedding_384', sa.Text, nullable=True),  # Will use vector type after pgvector migration
    )
    op.create_index('ix_industry_name', 'industry_entity', ['name'])


def downgrade() -> None:
    """
    Drop all entity tables.
    """
    op.drop_index('ix_industry_name', 'industry_entity')
    op.drop_table('industry_entity')
    
    op.drop_index('ix_agent_industry_id', 'agent_entity')
    op.drop_index('ix_agent_name', 'agent_entity')
    op.drop_table('agent_entity')
    
    op.drop_index('ix_team_job_role_id', 'team_entity')
    op.drop_index('ix_team_name', 'team_entity')
    op.drop_table('team_entity')
    
    op.drop_index('ix_job_role_seniority_level', 'job_role_entity')
    op.drop_index('ix_job_role_name', 'job_role_entity')
    op.drop_table('job_role_entity')
