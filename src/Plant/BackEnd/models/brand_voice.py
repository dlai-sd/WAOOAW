"""BrandVoiceModel — customer-specific brand voice definition.

PLANT-DMA-2 E4-S1

One row per customer. Drives content generation tone and vocabulary.
Upsert-safe on customer_id.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class BrandVoiceModel(Base):
    __tablename__ = "brand_voices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False, unique=True, index=True)
    tone_keywords = Column(JSONB, nullable=False, default=list)
    vocabulary_preferences = Column(JSONB, nullable=False, default=list)
    messaging_patterns = Column(JSONB, nullable=False, default=list)
    example_phrases = Column(JSONB, nullable=False, default=list)
    voice_description = Column(Text, nullable=False, default="")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        now = datetime.now(timezone.utc)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.tone_keywords is None:
            self.tone_keywords = []
        if self.vocabulary_preferences is None:
            self.vocabulary_preferences = []
        if self.messaging_patterns is None:
            self.messaging_patterns = []
        if self.example_phrases is None:
            self.example_phrases = []
        if self.voice_description is None:
            self.voice_description = ""
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
