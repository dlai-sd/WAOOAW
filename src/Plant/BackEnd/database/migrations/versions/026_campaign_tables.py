"""create_campaign_tables

Revision ID: 026_campaign_tables
Revises: 025_agent_skill_goal_config
Create Date: 2026-03-06

Stories: PLANT-CONTENT-2 E1-S2 — Alembic migration 026
Purpose: Create campaigns, daily_theme_items, and content_posts tables
         to persist the Campaign, DailyThemeItem, and ContentPost Pydantic
         models from agent_mold/skills/content_models.py.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "026_campaign_tables"
down_revision = "025_agent_skill_goal_config"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Create campaigns, daily_theme_items, and content_posts tables."""

    # ── campaigns ──────────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("hired_instance_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column(
            "brief",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "cost_estimate",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("campaign_id", name="pk_campaigns"),
        sa.ForeignKeyConstraint(
            ["hired_instance_id"],
            ["hired_agents.hired_instance_id"],
            name="fk_campaigns_hired_instance",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_campaigns_hired_instance_id", "campaigns", ["hired_instance_id"]
    )
    op.create_index("ix_campaigns_customer_id", "campaigns", ["customer_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_created_at", "campaigns", ["created_at"])

    # ── daily_theme_items ──────────────────────────────────────────────────
    op.create_table(
        "daily_theme_items",
        sa.Column("theme_item_id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("theme_title", sa.String(), nullable=False),
        sa.Column("theme_description", sa.Text(), nullable=False),
        sa.Column(
            "dimensions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "review_status",
            sa.String(),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("theme_item_id", name="pk_daily_theme_items"),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.campaign_id"],
            name="fk_daily_theme_items_campaign",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_daily_theme_items_campaign_id", "daily_theme_items", ["campaign_id"]
    )
    op.create_index(
        "ix_daily_theme_items_campaign_day",
        "daily_theme_items",
        ["campaign_id", "day_number"],
    )
    op.create_index(
        "ix_daily_theme_items_review_status",
        "daily_theme_items",
        ["review_status"],
    )

    # ── content_posts ──────────────────────────────────────────────────────
    op.create_table(
        "content_posts",
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("theme_item_id", sa.String(), nullable=False),
        sa.Column(
            "destination",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column(
            "hashtags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "scheduled_publish_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "review_status",
            sa.String(),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column(
            "publish_status",
            sa.String(),
            nullable=False,
            server_default="not_published",
        ),
        sa.Column(
            "publish_receipt",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("post_id", name="pk_content_posts"),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.campaign_id"],
            name="fk_content_posts_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["theme_item_id"],
            ["daily_theme_items.theme_item_id"],
            name="fk_content_posts_theme_item",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_content_posts_campaign_id", "content_posts", ["campaign_id"]
    )
    op.create_index(
        "ix_content_posts_theme_item_id", "content_posts", ["theme_item_id"]
    )
    op.create_index(
        "ix_content_posts_review_status", "content_posts", ["review_status"]
    )
    op.create_index(
        "ix_content_posts_publish_status", "content_posts", ["publish_status"]
    )
    op.create_index(
        "ix_content_posts_scheduled_publish_at",
        "content_posts",
        ["scheduled_publish_at"],
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Drop content_posts, daily_theme_items, campaigns tables (reverse order)."""

    # content_posts
    op.drop_index("ix_content_posts_scheduled_publish_at", table_name="content_posts")
    op.drop_index("ix_content_posts_publish_status", table_name="content_posts")
    op.drop_index("ix_content_posts_review_status", table_name="content_posts")
    op.drop_index("ix_content_posts_theme_item_id", table_name="content_posts")
    op.drop_index("ix_content_posts_campaign_id", table_name="content_posts")
    op.drop_table("content_posts")

    # daily_theme_items
    op.drop_index(
        "ix_daily_theme_items_review_status", table_name="daily_theme_items"
    )
    op.drop_index(
        "ix_daily_theme_items_campaign_day", table_name="daily_theme_items"
    )
    op.drop_index(
        "ix_daily_theme_items_campaign_id", table_name="daily_theme_items"
    )
    op.drop_table("daily_theme_items")

    # campaigns
    op.drop_index("ix_campaigns_created_at", table_name="campaigns")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaigns_customer_id", table_name="campaigns")
    op.drop_index("ix_campaigns_hired_instance_id", table_name="campaigns")
    op.drop_table("campaigns")
