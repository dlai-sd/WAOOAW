"""add_dma_media_artifact_persistence

Revision ID: 037_dma_media_artifact_persistence
Revises: 036_add_publish_receipts
Create Date: 2026-04-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "037_dma_media_artifact_persistence"
down_revision = "036_add_publish_receipts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_type", sa.String(length=32), nullable=False, server_default="text"),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_uri", sa.Text(), nullable=True),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_preview_uri", sa.Text(), nullable=True),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_mime_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column(
            "artifact_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_generation_status", sa.String(length=32), nullable=False, server_default="not_requested"),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column("artifact_job_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "marketing_draft_posts",
        sa.Column(
            "generated_artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_index("ix_marketing_draft_posts_artifact_type", "marketing_draft_posts", ["artifact_type"])
    op.create_index("ix_marketing_draft_posts_artifact_generation_status", "marketing_draft_posts", ["artifact_generation_status"])
    op.create_index("ix_marketing_draft_posts_artifact_job_id", "marketing_draft_posts", ["artifact_job_id"])


def downgrade() -> None:
    op.drop_index("ix_marketing_draft_posts_artifact_type", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_artifact_job_id", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_artifact_generation_status", table_name="marketing_draft_posts")
    op.drop_column("marketing_draft_posts", "generated_artifacts")
    op.drop_column("marketing_draft_posts", "artifact_job_id")
    op.drop_column("marketing_draft_posts", "artifact_generation_status")
    op.drop_column("marketing_draft_posts", "artifact_metadata")
    op.drop_column("marketing_draft_posts", "artifact_mime_type")
    op.drop_column("marketing_draft_posts", "artifact_preview_uri")
    op.drop_column("marketing_draft_posts", "artifact_uri")
    op.drop_column("marketing_draft_posts", "artifact_type")