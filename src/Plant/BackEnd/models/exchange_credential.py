"""ExchangeCredentialModel — Plant DB record for customer exchange API credentials.

TRADER-FULL-1 S1.
Secrets are stored Fernet-encrypted (dev/demo) or as a GCP Secret Manager ref (prod).
EXCHANGE_SECRET_BACKEND env var = "fernet" | "secret_manager" — never baked into image.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class ExchangeCredentialModel(Base):
    __tablename__ = "exchange_credentials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    credential_ref = Column(String(255), nullable=False, unique=True, index=True)
    exchange_provider = Column(String(100), nullable=False, default="delta_exchange_india")
    # Fernet-encrypted API key blob OR "sm:<secret_manager_ref>" prefix for prod
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    default_coin = Column(String(50), nullable=False)
    allowed_coins = Column(JSONB, nullable=False, default=list)
    risk_limits = Column(JSONB, nullable=False, default=dict)
    # "pending" | "valid" | "invalid"
    validation_status = Column(String(50), nullable=False, default="pending")
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
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

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "exchange_provider",
            name="uq_exchange_credentials_customer_provider",
        ),
        Index("ix_exchange_credentials_customer_id", "customer_id"),
    )
