"""Customer entity.

REG-1.5: Plant stores customer identity + business profile, with lookup by email
and idempotent create.

This uses the Plant BaseEntity inheritance model so customer records participate
in the same lifecycle + audit primitives as other entities.

E3-S1 (Iteration 7): email, phone, full_name are stored encrypted via
EncryptedString TypeDecorator (AES-256-GCM).  Lookups are done via email_hash
(HMAC-SHA256 of the normalised email) to avoid full-table scans.

When ENCRYPTION_KEY env var is not set (local dev / CI without the key),
EncryptedString behaves as plain String — no behaviour change.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from core.encryption import EncryptedString  # E3-S1 (Iteration 7)
from models.base_entity import BaseEntity


class Customer(BaseEntity):
    """Customer identity + business profile."""

    __tablename__ = "customer_entity"
    __mapper_args__ = {"polymorphic_identity": "Customer"}

    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)

    # Identity — stored encrypted at rest (E3-S1 Iteration 7)
    # email and phone keep unique=True for backwards compat; in encrypted mode
    # uniqueness is enforced at the application layer via email_hash lookups.
    email = Column(EncryptedString(1024), nullable=False, unique=True)
    phone = Column(EncryptedString(512), nullable=False, unique=True)

    # Deterministic search index for email (HMAC-SHA256) — E3-S1
    # Populated on every write by the service layer via email_search_hash().
    email_hash = Column(String(64), nullable=True, index=True)

    # Profile
    full_name = Column(EncryptedString(1024), nullable=False)
    business_name = Column(String(255), nullable=False)
    business_industry = Column(String(100), nullable=False)
    business_address = Column(Text, nullable=False)

    website = Column(String(500), nullable=True)
    gst_number = Column(String(20), nullable=True)

    preferred_contact_method = Column(String(20), nullable=False)
    consent = Column(Boolean, nullable=False, default=False)

    # E2-S3: token version — incremented on password reset to invalidate all sessions
    token_version = Column(Integer, nullable=False, default=1, server_default="1")

    __table_args__ = (
        Index("ix_customer_email", "email"),
        Index("ix_customer_phone", "phone"),
        Index("ix_customer_email_hash", "email_hash"),
    )

