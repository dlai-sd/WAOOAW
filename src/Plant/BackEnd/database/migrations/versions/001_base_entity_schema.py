"""
Create base_entity table with all 7 sections

Revision ID: 001_base_entity
Revises: 
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON

# revision identifiers
revision = '001_base_entity'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create base_entity table with all 7 sections:
    1. Identity
    2. Lifecycle
    3. Versioning
    4. Constitutional Alignment
    5. Audit Trail
    6. Metadata
    7. Relationships
    """
    
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # Create base_entity table
    op.create_table(
        'base_entity',
        # SECTION 1: IDENTITY
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=True, unique=True),
        
        # SECTION 2: LIFECYCLE
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        
        # SECTION 3: VERSIONING
        sa.Column('version_hash', sa.String(64), nullable=False),
        sa.Column('amendment_history', JSON, nullable=False, server_default='[]'),
        sa.Column('evolution_markers', JSON, nullable=False, server_default='{}'),
        
        # SECTION 4: CONSTITUTIONAL ALIGNMENT
        sa.Column('l0_compliance_status', JSON, nullable=False, server_default='{}'),
        sa.Column('amendment_alignment', sa.String(20), nullable=False, server_default='aligned'),
        sa.Column('drift_detector', JSON, nullable=False, server_default='{}'),
        
        # SECTION 5: AUDIT TRAIL
        sa.Column('append_only', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('hash_chain_sha256', ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('tamper_proof', sa.Boolean, nullable=False, server_default='true'),
        
        # SECTION 6: METADATA
        sa.Column('tags', ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('custom_attributes', JSON, nullable=False, server_default='{}'),
        sa.Column('governance_notes', sa.Text, nullable=True),
        
        # SECTION 7: RELATIONSHIPS
        sa.Column('parent_id', UUID(as_uuid=True), nullable=True),
        sa.Column('child_ids', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('governance_agent_id', sa.String(100), nullable=False, server_default='genesis'),
    )
    
    # Create indexes
    op.create_index('ix_base_entity_entity_type', 'base_entity', ['entity_type'])
    op.create_index('ix_base_entity_created_at', 'base_entity', ['created_at'])
    op.create_index('ix_base_entity_status', 'base_entity', ['status'])
    op.create_index('ix_base_entity_governance_agent_id', 'base_entity', ['governance_agent_id'])
    
    # Create trigger to prevent UPDATE on audit columns (append-only enforcement)
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_column_updates()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.created_at IS DISTINCT FROM NEW.created_at THEN
                RAISE EXCEPTION 'created_at is immutable (append-only violation)';
            END IF;
            IF OLD.hash_chain_sha256 != NEW.hash_chain_sha256 AND 
               array_length(OLD.hash_chain_sha256, 1) < array_length(NEW.hash_chain_sha256, 1) THEN
                -- Allow appending to hash chain only
                RETURN NEW;
            ELSIF OLD.hash_chain_sha256 != NEW.hash_chain_sha256 THEN
                RAISE EXCEPTION 'hash_chain_sha256 modification not allowed (append-only violation)';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER base_entity_audit_immutability
        BEFORE UPDATE ON base_entity
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_column_updates();
    """)


def downgrade() -> None:
    """
    Drop base_entity table and related objects.
    """
    op.execute('DROP TRIGGER IF EXISTS base_entity_audit_immutability ON base_entity;')
    op.execute('DROP FUNCTION IF EXISTS prevent_audit_column_updates();')
    op.drop_index('ix_base_entity_governance_agent_id', 'base_entity')
    op.drop_index('ix_base_entity_status', 'base_entity')
    op.drop_index('ix_base_entity_created_at', 'base_entity')
    op.drop_index('ix_base_entity_entity_type', 'base_entity')
    op.drop_table('base_entity')
