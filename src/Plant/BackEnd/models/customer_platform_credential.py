from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class CustomerPlatformCredentialModel(Base):
    __tablename__ = "customer_platform_credentials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    platform_key = Column(String(100), nullable=False)
    provider_account_id = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    granted_scopes = Column(JSONB, nullable=False, default=list)
    verification_status = Column(String(50), nullable=False, default="pending")
    connection_status = Column(String(50), nullable=False, default="pending")
    secret_ref = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
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
            "customer_id",
            "platform_key",
            "provider_account_id",
            name="uq_customer_platform_credential_customer_platform_provider",
        ),
        Index("ix_customer_platform_credentials_customer_id", "customer_id"),
        Index("ix_customer_platform_credentials_platform_key", "platform_key"),
    )