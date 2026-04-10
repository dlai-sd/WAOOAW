"""add_brand_voices

Revision ID: 038_add_brand_voices
Revises: 037_dma_media_artifact_persistence
Create Date: 2026-04-10

Creates the brand_voices table — one row per customer, drives DMA content
generation tone and vocabulary.  The model existed without a migration,
causing UndefinedTableError on first brand-voice read after deploy.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "038_add_brand_voices"
down_revision = "037_dma_media_artifact_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brand_voices",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("tone_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("vocabulary_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("messaging_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("example_phrases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("voice_description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_id"),
    )
    op.create_index("ix_brand_voices_customer_id", "brand_voices", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_brand_voices_customer_id", table_name="brand_voices")
    op.drop_table("brand_voices")
