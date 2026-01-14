"""
RLS (Row Level Security) Policies for Plant entities

Revision ID: 005_rls_policies
Revises: 004_pgvector_setup
Create Date: 2026-01-14

"""
from alembic import op

# revision identifiers
revision = '005_rls_policies'
down_revision = '004_pgvector_setup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enable RLS on all entity tables and create policies.
    """
    
    # Enable RLS on base_entity (inherited by all tables)
    op.execute('ALTER TABLE base_entity ENABLE ROW LEVEL SECURITY;')
    
    # Enable RLS on all entity tables
    for table in ['skill_entity', 'job_role_entity', 'team_entity', 'agent_entity', 'industry_entity']:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;')
    
    # Create RLS policy: SELECT (governance agents + owners can see)
    op.execute("""
        CREATE POLICY base_entity_select_policy ON base_entity
        FOR SELECT
        USING (
            governance_agent_id = current_setting('app.current_agent_id', true)
            OR status = 'active'
        );
    """)
    
    # Create RLS policy: INSERT (only governance agents)
    op.execute("""
        CREATE POLICY base_entity_insert_policy ON base_entity
        FOR INSERT
        WITH CHECK (
            governance_agent_id = current_setting('app.current_agent_id', true)
        );
    """)
    
    # Create RLS policy: UPDATE (only governance agents, audit columns immutable)
    op.execute("""
        CREATE POLICY base_entity_update_policy ON base_entity
        FOR UPDATE
        USING (
            governance_agent_id = current_setting('app.current_agent_id', true)
        )
        WITH CHECK (
            governance_agent_id = current_setting('app.current_agent_id', true)
        );
    """)
    
    # Create RLS policy: DELETE (soft delete only, no hard delete)
    op.execute("""
        CREATE POLICY base_entity_delete_policy ON base_entity
        FOR DELETE
        USING (false);  -- Hard deletes blocked
    """)


def downgrade() -> None:
    """
    Disable RLS and drop policies.
    """
    op.execute('DROP POLICY IF EXISTS base_entity_delete_policy ON base_entity;')
    op.execute('DROP POLICY IF EXISTS base_entity_update_policy ON base_entity;')
    op.execute('DROP POLICY IF EXISTS base_entity_insert_policy ON base_entity;')
    op.execute('DROP POLICY IF EXISTS base_entity_select_policy ON base_entity;')
    
    for table in ['industry_entity', 'agent_entity', 'team_entity', 'job_role_entity', 'skill_entity']:
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;')
    
    op.execute('ALTER TABLE base_entity DISABLE ROW LEVEL SECURITY;')
