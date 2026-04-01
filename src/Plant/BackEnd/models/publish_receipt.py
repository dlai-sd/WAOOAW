"""PublishReceiptModel — persisted record of every publish attempt.

PLANT-DMA-2 E2-S1

One row per publish attempt. Links to a campaign post by post_id.
Unique per (post_id, destination_type) — upsert-safe.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class PublishReceiptModel(Base):
    __tablename__ = "publish_receipts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, nullable=False, index=True)
    destination_type = Column(String, nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    platform_post_id = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    raw_response = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_publish_receipts_post_dest", "post_id", "destination_type"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
