from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class MarketingDraftBatchModel(Base):
    __tablename__ = "marketing_draft_batches"

    batch_id = Column(String, primary_key=True, nullable=False)
    agent_id = Column(String, nullable=False, index=True)
    hired_instance_id = Column(
        String,
        nullable=True,
    )
    campaign_id = Column(
        String,
        nullable=True,
        index=True,
    )
    customer_id = Column(String, nullable=True, index=True)
    theme = Column(Text, nullable=False)
    brand_name = Column(Text, nullable=False)
    brief_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=False, default="pending_review", index=True)
    workflow_state = Column(String(64), nullable=False, default="draft_ready_for_review")

    posts = relationship(
        "MarketingDraftPostModel",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="MarketingDraftPostModel.created_at",
    )

    __table_args__ = (
        Index("ix_marketing_draft_batches_created_at", "created_at"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class MarketingDraftPostModel(Base):
    __tablename__ = "marketing_draft_posts"

    post_id = Column(String, primary_key=True, nullable=False)
    batch_id = Column(
        String,
        ForeignKey("marketing_draft_batches.batch_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id = Column(
        String,
        nullable=True,
        index=True,
    )
    channel = Column(String(64), nullable=False)
    text = Column(Text, nullable=False)
    hashtags = Column(JSONB, nullable=False, default=list)
    artifact_type = Column(String(32), nullable=False, default="text", index=True)
    artifact_uri = Column(Text, nullable=True)
    artifact_preview_uri = Column(Text, nullable=True)
    artifact_mime_type = Column(String(255), nullable=True)
    artifact_metadata = Column(JSONB, nullable=False, default=dict)
    artifact_generation_status = Column(String(32), nullable=False, default="not_requested", index=True)
    artifact_job_id = Column(String(255), nullable=True, index=True)
    generated_artifacts = Column(JSONB, nullable=False, default=list)
    review_status = Column(String(32), nullable=False, default="pending_review", index=True)
    approval_id = Column(String(255), nullable=True, index=True)
    credential_ref = Column(Text, nullable=True)
    execution_status = Column(String(32), nullable=False, default="not_scheduled", index=True)
    visibility = Column(String(32), nullable=False, default="private")
    public_release_requested = Column(Boolean, nullable=False, default=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    provider_post_id = Column(String(255), nullable=True)
    provider_post_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    batch = relationship("MarketingDraftBatchModel", back_populates="posts")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now