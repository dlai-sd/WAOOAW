"""Create trials and trial_deliverables tables

Revision ID: 006_trial_tables
Revises: 005_rls_policies
Create Date: 2026-01-17 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_trial_tables'
down_revision = '005_rls_policies'
branch_labels = None
depends_on = None


def upgrade():
    """Create trials and trial_deliverables tables for Agent Trial feature (PR #127)"""
    
    # Create trials table
    op.create_table(
        'trials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.ForeignKeyConstraint(['agent_id'], ['agent_entity.id'], name='fk_trials_agent_id', ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('active', 'converted', 'cancelled', 'expired')", name='ck_trials_status'),
        sa.CheckConstraint('end_date > start_date', name='ck_trials_date_range'),
    )
    
    # Create indexes for trials
    op.create_index('idx_trials_agent_id', 'trials', ['agent_id'])
    op.create_index('idx_trials_customer_email', 'trials', ['customer_email'])
    op.create_index('idx_trials_status', 'trials', ['status'])
    op.create_index('idx_trials_start_date', 'trials', ['start_date'])
    
    # Create trial_deliverables table
    op.create_table(
        'trial_deliverables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('trial_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], name='fk_trial_deliverables_trial_id', ondelete='CASCADE'),
    )
    
    # Create indexes for trial_deliverables
    op.create_index('idx_trial_deliverables_trial_id', 'trial_deliverables', ['trial_id'])
    op.create_index('idx_trial_deliverables_created_at', 'trial_deliverables', ['created_at'])


def downgrade():
    """Drop trials and trial_deliverables tables"""
    
    # Drop indexes first
    op.drop_index('idx_trial_deliverables_created_at', table_name='trial_deliverables')
    op.drop_index('idx_trial_deliverables_trial_id', table_name='trial_deliverables')
    
    # Drop trial_deliverables table
    op.drop_table('trial_deliverables')
    
    # Drop trials indexes
    op.drop_index('idx_trials_start_date', table_name='trials')
    op.drop_index('idx_trials_status', table_name='trials')
    op.drop_index('idx_trials_customer_email', table_name='trials')
    op.drop_index('idx_trials_agent_id', table_name='trials')
    
    # Drop trials table
    op.drop_table('trials')
