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

    # pgvector is optional in our lean Postgres test container.
    # If the extension isn't available, skip the type conversions/indexes.
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                CREATE EXTENSION IF NOT EXISTS vector;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'pgvector extension not available; skipping vector column conversions.';
                RETURN;
            END;

            -- Convert embedding columns to vector types
            BEGIN
                ALTER TABLE skill_entity
                    ALTER COLUMN embedding_384 TYPE vector(384)
                    USING embedding_384::vector;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Skipping skill_entity.embedding_384 conversion.';
            END;

            BEGIN
                ALTER TABLE industry_entity
                    ALTER COLUMN embedding_384 TYPE vector(384)
                    USING embedding_384::vector;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Skipping industry_entity.embedding_384 conversion.';
            END;

            -- Create IVFFlat indexes (optional)
            BEGIN
                CREATE INDEX IF NOT EXISTS skill_embedding_ivfflat_idx
                    ON skill_entity
                    USING ivfflat (embedding_384 vector_cosine_ops)
                    WITH (lists = 100);
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Skipping skill_embedding_ivfflat_idx creation.';
            END;

            BEGIN
                CREATE INDEX IF NOT EXISTS industry_embedding_ivfflat_idx
                    ON industry_entity
                    USING ivfflat (embedding_384 vector_cosine_ops)
                    WITH (lists = 100);
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Skipping industry_embedding_ivfflat_idx creation.';
            END;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove pgvector indexes and revert to text columns.
    """
    op.execute('DROP INDEX IF EXISTS skill_embedding_ivfflat_idx;')
    op.execute('DROP INDEX IF EXISTS industry_embedding_ivfflat_idx;')
    
    op.execute('ALTER TABLE skill_entity ALTER COLUMN embedding_384 TYPE text;')
    op.execute('ALTER TABLE industry_entity ALTER COLUMN embedding_384 TYPE text;')
