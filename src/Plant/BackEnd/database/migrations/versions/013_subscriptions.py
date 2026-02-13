"""create_subscriptions_table

Revision ID: b906e19d2162
Revises: 08f0843920f5
Create Date: 2026-02-11 11:23:17.345457

Story: AGP1-DB-4.2 - Create DB table for subscriptions scaffolding
Purpose: Replace payments_simple.py _SubscriptionRecord in-memory storage
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b906e19d2162'
down_revision = '08f0843920f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create subscriptions table."""
    
    op.create_table(
        'subscriptions',
        sa.Column('subscription_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('duration', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('subscription_id', name='pk_subscriptions')
    )
    
    # Create indexes
    op.create_index('ix_subscriptions_agent_id', 'subscriptions', ['agent_id'], unique=False)
    op.create_index('ix_subscriptions_customer_id', 'subscriptions', ['customer_id'], unique=False)
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'], unique=False)


def downgrade() -> None:
    """Drop subscriptions table."""
    
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_customer_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_agent_id', table_name='subscriptions')
    op.drop_table('subscriptions')

