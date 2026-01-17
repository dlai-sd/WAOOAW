"""
Create gateway_audit_logs table with RLS and indexes

Revision ID: 007_gateway_audit_logs
Revises: 006_trial_tables
Create Date: 2026-01-17

Purpose: Track all gateway requests, OPA decisions, and constitutional context
Retention: 90 days (automated cleanup via pg_cron)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers
revision = '007_gateway_audit_logs'
down_revision = '006_trial_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create gateway_audit_logs table with comprehensive tracking for:
    - Request/response metadata
    - OPA policy decisions
    - Constitutional context (governor role, trial mode)
    - Performance metrics
    - Distributed tracing (correlation_id, causation_id)
    """
    
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_cron";')
    
    # Create audit logs table
    op.create_table(
        'gateway_audit_logs',
        
        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        
        # Tracing IDs (distributed tracing)
        sa.Column('correlation_id', UUID(as_uuid=True), nullable=False, 
                  comment='Trace ID spanning multiple requests'),
        sa.Column('causation_id', UUID(as_uuid=True), nullable=True,
                  comment='Parent request ID (null for root requests)'),
        
        # Timestamp
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Request metadata
        sa.Column('gateway_type', sa.String(10), nullable=False),
        sa.Column('request_id', sa.String(100), nullable=False),
        sa.Column('http_method', sa.String(10), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('query_params', JSONB, nullable=True),
        sa.Column('request_headers', JSONB, nullable=True),
        sa.Column('request_body', JSONB, nullable=True),
        
        # User context (constitutional context)
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('roles', ARRAY(sa.String), nullable=True),
        sa.Column('trial_mode', sa.Boolean, nullable=False, server_default='false'),
        
        # OPA policy decisions
        sa.Column('opa_policies_evaluated', ARRAY(sa.String), nullable=True,
                  comment='List of policy names evaluated'),
        sa.Column('opa_decisions', JSONB, nullable=True,
                  comment='Policy results: {policy_name: {allow: bool, deny_reason: str}}'),
        sa.Column('opa_latency_ms', sa.Integer, nullable=True),
        
        # Response metadata
        sa.Column('status_code', sa.Integer, nullable=True),
        sa.Column('response_headers', JSONB, nullable=True),
        sa.Column('response_body', JSONB, nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Performance metrics
        sa.Column('total_latency_ms', sa.Integer, nullable=False),
        sa.Column('plant_latency_ms', sa.Integer, nullable=True),
        
        # Resource tracking
        sa.Column('action', sa.String(100), nullable=True),
        sa.Column('resource', sa.String(100), nullable=True),
        sa.Column('resource_id', UUID(as_uuid=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint('gateway_type IN (\'CP\', \'PP\')', name='valid_gateway_type'),
        sa.CheckConstraint('status_code >= 100 AND status_code < 600', name='valid_status_code'),
        sa.CheckConstraint('total_latency_ms >= 0', name='valid_latency'),
    )
    
    # Create indexes for fast queries
    
    # Tracing queries (find all requests in a trace)
    op.create_index('idx_audit_correlation_id', 'gateway_audit_logs', ['correlation_id'])
    op.create_index('idx_audit_causation_id', 'gateway_audit_logs', ['causation_id'], 
                    postgresql_where=sa.text('causation_id IS NOT NULL'))
    
    # User queries (find all actions by a user)
    op.create_index('idx_audit_user_id', 'gateway_audit_logs', ['user_id'])
    op.create_index('idx_audit_customer_id', 'gateway_audit_logs', ['customer_id'],
                    postgresql_where=sa.text('customer_id IS NOT NULL'))
    
    # Time-based queries (recent logs, time-range analytics)
    op.create_index('idx_audit_timestamp', 'gateway_audit_logs', [sa.text('timestamp DESC')])
    
    # Error queries (find failed requests)
    op.create_index('idx_audit_errors', 'gateway_audit_logs', ['status_code', 'error_type'],
                    postgresql_where=sa.text('status_code >= 400'))
    
    # Policy decision queries (find OPA denies) - GIN index for JSONB
    op.create_index('idx_audit_opa_decisions', 'gateway_audit_logs', ['opa_decisions'],
                    postgresql_using='gin')
    
    # Gateway type queries (CP vs PP)
    op.create_index('idx_audit_gateway_type', 'gateway_audit_logs', ['gateway_type'])
    
    # Action/Resource queries (audit specific actions)
    op.create_index('idx_audit_action_resource', 'gateway_audit_logs', ['action', 'resource'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_audit_user_timestamp', 'gateway_audit_logs', 
                    ['user_id', sa.text('timestamp DESC')])
    op.create_index('idx_audit_customer_timestamp', 'gateway_audit_logs',
                    ['customer_id', sa.text('timestamp DESC')],
                    postgresql_where=sa.text('customer_id IS NOT NULL'))
    
    # Enable Row-Level Security (RLS)
    op.execute('ALTER TABLE gateway_audit_logs ENABLE ROW LEVEL SECURITY;')
    
    # RLS Policy 1: Admins can see all logs
    op.execute("""
        CREATE POLICY admin_all_access ON gateway_audit_logs
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_admin', true)::boolean = true
        );
    """)
    
    # RLS Policy 2: Users can only see their own logs
    op.execute("""
        CREATE POLICY user_own_logs ON gateway_audit_logs
        FOR SELECT
        TO PUBLIC
        USING (
            user_id::text = current_setting('app.current_user_id', true)
        );
    """)
    
    # RLS Policy 3: Customer admins can see logs for their customer
    op.execute("""
        CREATE POLICY customer_admin_logs ON gateway_audit_logs
        FOR SELECT
        TO PUBLIC
        USING (
            customer_id::text = current_setting('app.current_customer_id', true)
            AND current_setting('app.is_customer_admin', true)::boolean = true
        );
    """)
    
    # RLS Policy 4: System service accounts (gateway, OPA) can insert logs
    op.execute("""
        CREATE POLICY system_insert_logs ON gateway_audit_logs
        FOR INSERT
        TO PUBLIC
        WITH CHECK (
            current_setting('app.service_account', true) IN ('gateway', 'opa')
        );
    """)
    
    # Automated cleanup: Delete logs older than 90 days
    # Runs daily at 2 AM UTC
    op.execute("""
        SELECT cron.schedule(
            'gateway_audit_logs_cleanup',
            '0 2 * * *',
            $$DELETE FROM gateway_audit_logs WHERE timestamp < NOW() - INTERVAL '90 days'$$
        );
    """)


def downgrade() -> None:
    """
    Drop gateway_audit_logs table and cleanup cron job.
    """
    
    # Remove cron job
    op.execute("SELECT cron.unschedule('gateway_audit_logs_cleanup');")
    
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS system_insert_logs ON gateway_audit_logs;')
    op.execute('DROP POLICY IF EXISTS customer_admin_logs ON gateway_audit_logs;')
    op.execute('DROP POLICY IF EXISTS user_own_logs ON gateway_audit_logs;')
    op.execute('DROP POLICY IF EXISTS admin_all_access ON gateway_audit_logs;')
    
    # Drop indexes (automatically dropped with table, but explicit for clarity)
    op.drop_index('idx_audit_customer_timestamp', 'gateway_audit_logs')
    op.drop_index('idx_audit_user_timestamp', 'gateway_audit_logs')
    op.drop_index('idx_audit_action_resource', 'gateway_audit_logs')
    op.drop_index('idx_audit_gateway_type', 'gateway_audit_logs')
    op.drop_index('idx_audit_opa_decisions', 'gateway_audit_logs')
    op.drop_index('idx_audit_errors', 'gateway_audit_logs')
    op.drop_index('idx_audit_timestamp', 'gateway_audit_logs')
    op.drop_index('idx_audit_customer_id', 'gateway_audit_logs')
    op.drop_index('idx_audit_user_id', 'gateway_audit_logs')
    op.drop_index('idx_audit_causation_id', 'gateway_audit_logs')
    op.drop_index('idx_audit_correlation_id', 'gateway_audit_logs')
    
    # Drop table
    op.drop_table('gateway_audit_logs')

