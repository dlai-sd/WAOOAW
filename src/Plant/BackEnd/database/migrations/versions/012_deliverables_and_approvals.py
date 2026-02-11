"""create_deliverables_and_approvals_tables

Revision ID: 08f0843920f5
Revises: bb0ee0250f8a
Create Date: 2026-02-11 11:05:22.703960

Stories: AGP1-DB-3.1 & AGP1-DB-3.2 - Create DB models for Deliverables and Approvals
Purpose: Move deliverables_simple.py in-memory state to DB persistence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '08f0843920f5'
down_revision = 'bb0ee0250f8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create deliverables and approvals tables."""
    
    # Create deliverables table
    op.create_table(
        'deliverables',
        sa.Column('deliverable_id', sa.String(), nullable=False),
        sa.Column('hired_instance_id', sa.String(), nullable=False),
        sa.Column('goal_instance_id', sa.String(), nullable=False),
        sa.Column('goal_template_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('review_status', sa.String(), nullable=False, server_default='pending_review'),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('approval_id', sa.String(), nullable=True),
        sa.Column('execution_status', sa.String(), nullable=False, server_default='not_executed'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('deliverable_id', name='pk_deliverables'),
        sa.ForeignKeyConstraint(
            ['hired_instance_id'],
            ['hired_agents.hired_instance_id'],
            name='fk_deliverables_hired_instance',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['goal_instance_id'],
            ['goal_instances.goal_instance_id'],
            name='fk_deliverables_goal_instance',
            ondelete='CASCADE'
        ),
    )
    
    # Create indexes for deliverables
    op.create_index('ix_deliverables_hired_instance_id', 'deliverables', ['hired_instance_id'], unique=False)
    op.create_index('ix_deliverables_hired_instance_created', 'deliverables', ['hired_instance_id', 'created_at'], unique=False)
    op.create_index('ix_deliverables_goal_instance', 'deliverables', ['goal_instance_id'], unique=False)
    op.create_index('ix_deliverables_review_status', 'deliverables', ['review_status'], unique=False)
    
    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('approval_id', sa.String(), nullable=False),
        sa.Column('deliverable_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('approval_id', name='pk_approvals'),
        sa.ForeignKeyConstraint(
            ['deliverable_id'],
            ['deliverables.deliverable_id'],
            name='fk_approvals_deliverable',
            ondelete='CASCADE'
        ),
    )
    
    # Create indexes for approvals
    op.create_index('ix_approvals_deliverable', 'approvals', ['deliverable_id'], unique=False)
    op.create_index('ix_approvals_customer', 'approvals', ['customer_id'], unique=False)
    
    # Add FK constraint from deliverables.approval_id -> approvals.approval_id
    # Note: This is added AFTER approvals table exists to avoid circular dependency
    op.create_foreign_key(
        'fk_deliverables_approval_id',
        'deliverables',
        'approvals',
        ['approval_id'],
        ['approval_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Drop approvals and deliverables tables."""
    
    # Drop FK constraint from deliverables -> approvals first
    op.drop_constraint('fk_deliverables_approval_id', 'deliverables', type_='foreignkey')
    
    # Drop approvals table and indexes
    op.drop_index('ix_approvals_customer', table_name='approvals')
    op.drop_index('ix_approvals_deliverable', table_name='approvals')
    op.drop_table('approvals')
    
    # Drop deliverables table and indexes
    op.drop_index('ix_deliverables_review_status', table_name='deliverables')
    op.drop_index('ix_deliverables_goal_instance', table_name='deliverables')
    op.drop_index('ix_deliverables_hired_instance_created', table_name='deliverables')
    op.drop_index('ix_deliverables_hired_instance_id', table_name='deliverables')
    op.drop_table('deliverables')

