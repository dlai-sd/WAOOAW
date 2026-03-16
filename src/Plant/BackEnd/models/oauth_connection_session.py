from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint

from core.database import Base


class OAuthConnectionSessionModel(Base):
    __tablename__ = "oauth_connection_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    platform_key = Column(String(100), nullable=False)
    state = Column(String(255), nullable=False)
    nonce = Column(String(255), nullable=False)
    redirect_uri = Column(String(1024), nullable=False)
    code_verifier = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
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
        UniqueConstraint("state", name="uq_oauth_connection_sessions_state"),
        Index("ix_oauth_connection_sessions_customer_id", "customer_id"),
        Index("ix_oauth_connection_sessions_platform_key", "platform_key"),
    )