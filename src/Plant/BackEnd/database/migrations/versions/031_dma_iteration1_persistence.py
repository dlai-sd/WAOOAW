"""persist_dma_iteration1_runtime

Revision ID: 031_dma_iteration1_persistence
Revises: 030_add_definition_version_id
Create Date: 2026-03-11

Persist DMA Iteration 1 runtime fields and marketing draft batch tables.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "031_dma_iteration1_persistence"
down_revision = "030_add_definition_version_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("workflow_state", sa.String(length=64), nullable=False, server_default="brief_captured"),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "brief_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "approval_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{"pending_review_count": 0, "approved_count": 0, "rejected_count": 0}',
        ),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "draft_deliverables",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_index("ix_campaigns_workflow_state", "campaigns", ["workflow_state"])

    op.add_column("content_posts", sa.Column("approval_id", sa.String(length=255), nullable=True))
    op.add_column("content_posts", sa.Column("credential_ref", sa.Text(), nullable=True))
    op.add_column(
        "content_posts",
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="private"),
    )
    op.add_column(
        "content_posts",
        sa.Column("public_release_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_content_posts_approval_id", "content_posts", ["approval_id"])
    op.create_index(
        "ix_content_posts_campaign_review_publish",
        "content_posts",
        ["campaign_id", "review_status", "publish_status"],
    )

    op.execute(
        """
        UPDATE content_posts
        SET
            approval_id = COALESCE(NULLIF(destination #>> '{metadata,approval_id}', ''), approval_id),
            credential_ref = COALESCE(NULLIF(destination #>> '{metadata,credential_ref}', ''), credential_ref),
            visibility = COALESCE(NULLIF(destination #>> '{metadata,visibility}', ''), visibility, 'private'),
            public_release_requested = COALESCE(
                (destination #>> '{metadata,public_release_requested}')::boolean,
                public_release_requested,
                FALSE
            )
        """
    )

    op.create_table(
        "marketing_draft_batches",
        sa.Column("batch_id", sa.String(length=255), nullable=False),
        sa.Column("agent_id", sa.String(length=255), nullable=False),
        sa.Column("hired_instance_id", sa.String(length=255), nullable=True),
        sa.Column("campaign_id", sa.String(length=255), nullable=True),
        sa.Column("customer_id", sa.String(length=255), nullable=True),
        sa.Column("theme", sa.Text(), nullable=False),
        sa.Column("brand_name", sa.Text(), nullable=False),
        sa.Column("brief_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_review"),
        sa.Column("workflow_state", sa.String(length=64), nullable=False, server_default="draft_ready_for_review"),
        sa.PrimaryKeyConstraint("batch_id", name="pk_marketing_draft_batches"),
    )
    op.create_index("ix_marketing_draft_batches_agent_id", "marketing_draft_batches", ["agent_id"])
    op.create_index("ix_marketing_draft_batches_customer_id", "marketing_draft_batches", ["customer_id"])
    op.create_index("ix_marketing_draft_batches_campaign_id", "marketing_draft_batches", ["campaign_id"])
    op.create_index("ix_marketing_draft_batches_status", "marketing_draft_batches", ["status"])
    op.create_index("ix_marketing_draft_batches_created_at", "marketing_draft_batches", ["created_at"])

    op.create_table(
        "marketing_draft_posts",
        sa.Column("post_id", sa.String(length=255), nullable=False),
        sa.Column("batch_id", sa.String(length=255), nullable=False),
        sa.Column("campaign_id", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("hashtags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending_review"),
        sa.Column("approval_id", sa.String(length=255), nullable=True),
        sa.Column("credential_ref", sa.Text(), nullable=True),
        sa.Column("execution_status", sa.String(length=32), nullable=False, server_default="not_scheduled"),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="private"),
        sa.Column("public_release_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_post_id", sa.String(length=255), nullable=True),
        sa.Column("provider_post_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("post_id", name="pk_marketing_draft_posts"),
        sa.ForeignKeyConstraint(["batch_id"], ["marketing_draft_batches.batch_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_marketing_draft_posts_batch_id", "marketing_draft_posts", ["batch_id"])
    op.create_index("ix_marketing_draft_posts_campaign_id", "marketing_draft_posts", ["campaign_id"])
    op.create_index("ix_marketing_draft_posts_review_status", "marketing_draft_posts", ["review_status"])
    op.create_index("ix_marketing_draft_posts_execution_status", "marketing_draft_posts", ["execution_status"])
    op.create_index("ix_marketing_draft_posts_scheduled_at", "marketing_draft_posts", ["scheduled_at"])
    op.create_index("ix_marketing_draft_posts_approval_id", "marketing_draft_posts", ["approval_id"])


def downgrade() -> None:
    op.drop_index("ix_marketing_draft_posts_approval_id", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_scheduled_at", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_execution_status", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_review_status", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_campaign_id", table_name="marketing_draft_posts")
    op.drop_index("ix_marketing_draft_posts_batch_id", table_name="marketing_draft_posts")
    op.drop_table("marketing_draft_posts")

    op.drop_index("ix_marketing_draft_batches_created_at", table_name="marketing_draft_batches")
    op.drop_index("ix_marketing_draft_batches_status", table_name="marketing_draft_batches")
    op.drop_index("ix_marketing_draft_batches_campaign_id", table_name="marketing_draft_batches")
    op.drop_index("ix_marketing_draft_batches_customer_id", table_name="marketing_draft_batches")
    op.drop_index("ix_marketing_draft_batches_agent_id", table_name="marketing_draft_batches")
    op.drop_table("marketing_draft_batches")

    op.drop_index("ix_content_posts_campaign_review_publish", table_name="content_posts")
    op.drop_index("ix_content_posts_approval_id", table_name="content_posts")
    op.drop_column("content_posts", "public_release_requested")
    op.drop_column("content_posts", "visibility")
    op.drop_column("content_posts", "credential_ref")
    op.drop_column("content_posts", "approval_id")

    op.drop_index("ix_campaigns_workflow_state", table_name="campaigns")
    op.drop_column("campaigns", "draft_deliverables")
    op.drop_column("campaigns", "approval_state")
    op.drop_column("campaigns", "brief_summary")
    op.drop_column("campaigns", "workflow_state")