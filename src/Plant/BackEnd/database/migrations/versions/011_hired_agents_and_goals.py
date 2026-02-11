"""create_hired_agents_and_goal_instances_tables

Revision ID: bb0ee0250f8a
Revises: ce2ce3126c3b
Create Date: 2026-02-11 09:54:32.987611

Stories: AGP1-DB-2.1 & AGP1-DB-2.2 - Create DB models for HiredAgent and GoalInstance
Purpose: Move hired_agents_simple.py in-memory state to DB persistence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bb0ee0250f8a'
down_revision = 'ce2ce3126c3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create hired_agents and goal_instances tables."""
    
    # Create hired_agents table
    op.create_table(
        'hired_agents',
        sa.Column('hired_instance_id', sa.String(), nullable=False),
        sa.Column('subscription_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('nickname', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('configured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('goals_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('trial_status', sa.String(), nullable=False, server_default='not_started'),
        sa.Column('trial_start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('hired_instance_id', name='pk_hired_agents')
    )
    
    # Create indexes for hired_agents
    op.create_index('ix_hired_agents_subscription_id', 'hired_agents', ['subscription_id'], unique=True)
    op.create_index('ix_hired_agents_agent_id', 'hired_agents', ['agent_id'], unique=False)
    op.create_index('ix_hired_agents_customer_id', 'hired_agents', ['customer_id'], unique=False)
    op.create_index('ix_hired_agents_trial_status', 'hired_agents', ['trial_status'], unique=False)
    
    # Create goal_instances table
    op.create_table(
        'goal_instances',
        sa.Column('goal_instance_id', sa.String(), nullable=False),
        sa.Column('hired_instance_id', sa.String(), nullable=False),
        sa.Column('goal_template_id', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('goal_instance_id', name='pk_goal_instances'),
        sa.ForeignKeyConstraint(
            ['hired_instance_id'],
            ['hired_agents.hired_instance_id'],
            name='fk_goal_instances_hired_instance_id',
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint('goal_instance_id', name='uq_goal_instance_id')
    )
    
    # Create index for goal_instances
    op.create_index('ix_goal_instances_hired_instance_id', 'goal_instances', ['hired_instance_id'], unique=False)


def downgrade() -> None:
    """Drop goal_instances and hired_agents tables."""
    
    op.drop_index('ix_goal_instances_hired_instance_id', table_name='goal_instances')
    op.drop_table('goal_instances')
    
    op.drop_index('ix_hired_agents_trial_status', table_name='hired_agents')
    op.drop_index('ix_hired_agents_customer_id', table_name='hired_agents')
    op.drop_index('ix_hired_agents_agent_id', table_name='hired_agents')
    op.drop_index('ix_hired_agents_subscription_id', table_name='hired_agents')
    op.drop_table('hired_agents')
