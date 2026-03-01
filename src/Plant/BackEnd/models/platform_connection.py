"""PlatformConnection — stores external platform credential refs per HiredAgent + Skill.

PLANT-SKILLS-1 E2-S1

NEVER stores the actual secret value.
secret_ref is a GCP Secret Manager resource path:
  e.g. "projects/waooaw-oauth/secrets/hired-abc123-delta-exchange/versions/latest"
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint

from core.database import Base


class PlatformConnectionModel(Base):
    __tablename__ = "platform_connections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(String, nullable=False)
    # e.g. "delta_exchange", "instagram", "facebook"
    platform_key = Column(String(100), nullable=False)
    # GCP Secret Manager resource path ONLY — NEVER the actual secret value
    secret_ref = Column(Text, nullable=False)
    # pending | connected | error
    status = Column(String(50), nullable=False, default="pending")
    connected_at = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "hired_instance_id", "skill_id", "platform_key",
            name="uq_platform_conn_hired_skill_platform",
        ),
        Index("ix_platform_connections_hired_instance_id", "hired_instance_id"),
    )
