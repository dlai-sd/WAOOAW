"""
Setup pgvector for semantic search

Revision ID: 004_pgvector_setup
Revises: 003_remaining_entities
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004_pgvector_setup'
down_revision = '003_remaining_entities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enable pgvector extension and convert embedding columns to vector type.
    """
    
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # Convert skill_entity.embedding_384 to vector(384)
    op.execute('ALTER TABLE skill_entity ALTER COLUMN embedding_384 TYPE vector(384) USING embedding_384::vector;')
    
    # Convert industry_entity.embedding_384 to vector(384)
    op.execute('ALTER TABLE industry_entity ALTER COLUMN embedding_384 TYPE vector(384) USING embedding_384::vector;')
    
    # Create IVFFlat index for skill embeddings (fast similarity search)
    op.execute("""
        CREATE INDEX skill_embedding_ivfflat_idx 
        ON skill_entity 
        USING ivfflat (embedding_384 vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    # Create IVFFlat index for industry embeddings
    op.execute("""
        CREATE INDEX industry_embedding_ivfflat_idx 
        ON industry_entity 
        USING ivfflat (embedding_384 vector_cosine_ops)
        WITH (lists = 100);
    """)


def downgrade() -> None:
    """
    Remove pgvector indexes and revert to text columns.
    """
    op.execute('DROP INDEX IF EXISTS skill_embedding_ivfflat_idx;')
    op.execute('DROP INDEX IF EXISTS industry_embedding_ivfflat_idx;')
    
    op.execute('ALTER TABLE skill_entity ALTER COLUMN embedding_384 TYPE text;')
    op.execute('ALTER TABLE industry_entity ALTER COLUMN embedding_384 TYPE text;')
