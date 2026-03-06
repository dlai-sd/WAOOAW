"""SQLAlchemy ORM models for Campaign persistence.

Tables: campaigns, daily_theme_items, content_posts

These models persist the in-memory Pydantic models from
agent_mold/skills/content_models.py to the database.

References:
    PLANT-CONTENT-2-campaign-persistence.md — E1-S1
    models/deliverable.py — pattern for review_status fields
    models/hired_agent.py — pattern for FK relationships
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class CampaignModel(Base):
    """Persisted campaign record — maps 1-to-1 with the Campaign Pydantic model.

    Status lifecycle: draft → theme_approved → running → paused → completed
    """

    __tablename__ = "campaigns"

    # Primary key
    campaign_id = Column(String, primary_key=True, nullable=False)

    # Foreign key to hired agent instance
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Customer who owns this campaign
    customer_id = Column(String, nullable=False, index=True)

    # CampaignBrief serialised as JSONB
    brief = Column(JSONB, nullable=False)

    # CostEstimate serialised as JSONB
    cost_estimate = Column(JSONB, nullable=False)

    # Status lifecycle
    status = Column(String, nullable=False, default="draft", index=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    theme_items = relationship(
        "DailyThemeItemModel",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="DailyThemeItemModel.day_number",
    )
    posts = relationship(
        "ContentPostModel",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_campaigns_hired_instance_id", "hired_instance_id"),
        Index("ix_campaigns_customer_id", "customer_id"),
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_created_at", "created_at"),
    )

    def __init__(
        self,
        campaign_id: str,
        hired_instance_id: str,
        customer_id: str,
        brief: dict[str, Any],
        cost_estimate: dict[str, Any],
        status: str = "draft",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self.hired_instance_id = hired_instance_id
        self.customer_id = customer_id
        self.brief = brief
        self.cost_estimate = cost_estimate
        self.status = status
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def __repr__(self) -> str:
        return (
            f"<CampaignModel(campaign_id={self.campaign_id!r}, "
            f"customer_id={self.customer_id!r}, status={self.status!r})>"
        )


class DailyThemeItemModel(Base):
    """Persisted daily theme item — one row per day in a campaign.

    Review lifecycle: pending_review → approved | rejected
    """

    __tablename__ = "daily_theme_items"

    # Primary key
    theme_item_id = Column(String, primary_key=True, nullable=False)

    # Foreign key to campaign
    campaign_id = Column(
        String,
        ForeignKey("campaigns.campaign_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Day number within the campaign (1-based)
    day_number = Column(Integer, nullable=False)

    # ISO date for this theme day
    scheduled_date = Column(Date, nullable=False)

    # Theme content
    theme_title = Column(String, nullable=False)
    theme_description = Column(Text, nullable=False)

    # Extra content angles serialised as JSONB array
    dimensions = Column(JSONB, nullable=False, default=list)

    # Review state: pending_review | approved | rejected
    review_status = Column(String, nullable=False, default="pending_review", index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign = relationship("CampaignModel", back_populates="theme_items")
    posts = relationship(
        "ContentPostModel",
        back_populates="theme_item",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_daily_theme_items_campaign_id", "campaign_id"),
        Index("ix_daily_theme_items_campaign_day", "campaign_id", "day_number"),
        Index("ix_daily_theme_items_review_status", "review_status"),
    )

    def __init__(
        self,
        theme_item_id: str,
        campaign_id: str,
        day_number: int,
        scheduled_date: date,
        theme_title: str,
        theme_description: str,
        dimensions: list[str] | None = None,
        review_status: str = "pending_review",
        approved_at: datetime | None = None,
    ) -> None:
        self.theme_item_id = theme_item_id
        self.campaign_id = campaign_id
        self.day_number = day_number
        self.scheduled_date = scheduled_date
        self.theme_title = theme_title
        self.theme_description = theme_description
        self.dimensions = dimensions or []
        self.review_status = review_status
        self.approved_at = approved_at

    def __repr__(self) -> str:
        return (
            f"<DailyThemeItemModel(theme_item_id={self.theme_item_id!r}, "
            f"campaign_id={self.campaign_id!r}, day_number={self.day_number!r}, "
            f"review_status={self.review_status!r})>"
        )


class ContentPostModel(Base):
    """Persisted content post — one row per destination per theme item day.

    Review lifecycle:  pending_review → approved | rejected
    Publish lifecycle: not_published  → published | failed
    """

    __tablename__ = "content_posts"

    # Primary key
    post_id = Column(String, primary_key=True, nullable=False)

    # Foreign keys
    campaign_id = Column(
        String,
        ForeignKey("campaigns.campaign_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    theme_item_id = Column(
        String,
        ForeignKey("daily_theme_items.theme_item_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Destination descriptor serialised as JSONB
    destination = Column(JSONB, nullable=False)

    # Generated content
    content_text = Column(Text, nullable=False)
    hashtags = Column(JSONB, nullable=False, default=list)

    # Scheduling
    scheduled_publish_at = Column(DateTime(timezone=True), nullable=False)

    # Review state: pending_review | approved | rejected
    review_status = Column(String, nullable=False, default="pending_review", index=True)

    # Publish state: not_published | published | failed
    publish_status = Column(String, nullable=False, default="not_published", index=True)

    # Adapter-specific response JSON
    publish_receipt = Column(JSONB, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    campaign = relationship("CampaignModel", back_populates="posts")
    theme_item = relationship("DailyThemeItemModel", back_populates="posts")

    # Indexes
    __table_args__ = (
        Index("ix_content_posts_campaign_id", "campaign_id"),
        Index("ix_content_posts_theme_item_id", "theme_item_id"),
        Index("ix_content_posts_review_status", "review_status"),
        Index("ix_content_posts_publish_status", "publish_status"),
        Index("ix_content_posts_scheduled_publish_at", "scheduled_publish_at"),
    )

    def __init__(
        self,
        post_id: str,
        campaign_id: str,
        theme_item_id: str,
        destination: dict[str, Any],
        content_text: str,
        hashtags: list[str] | None = None,
        scheduled_publish_at: datetime | None = None,
        review_status: str = "pending_review",
        publish_status: str = "not_published",
        publish_receipt: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.post_id = post_id
        self.campaign_id = campaign_id
        self.theme_item_id = theme_item_id
        self.destination = destination
        self.content_text = content_text
        self.hashtags = hashtags or []
        now = datetime.now(timezone.utc)
        self.scheduled_publish_at = scheduled_publish_at or now
        self.review_status = review_status
        self.publish_status = publish_status
        self.publish_receipt = publish_receipt
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def __repr__(self) -> str:
        return (
            f"<ContentPostModel(post_id={self.post_id!r}, "
            f"campaign_id={self.campaign_id!r}, "
            f"review_status={self.review_status!r}, "
            f"publish_status={self.publish_status!r})>"
        )
