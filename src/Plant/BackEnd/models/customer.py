"""Customer entity.

REG-1.5: Plant stores customer identity + business profile, with lookup by email
and idempotent create.

This uses the Plant BaseEntity inheritance model so customer records participate
in the same lifecycle + audit primitives as other entities.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from models.base_entity import BaseEntity


class Customer(BaseEntity):
    """Customer identity + business profile."""

    __tablename__ = "customer_entity"
    __mapper_args__ = {"polymorphic_identity": "Customer"}

    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)

    # Identity
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=False)
    business_industry = Column(String(100), nullable=False)
    business_address = Column(Text, nullable=False)

    website = Column(String(500), nullable=True)
    gst_number = Column(String(20), nullable=True)

    preferred_contact_method = Column(String(20), nullable=False)
    consent = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_customer_email", "email"),
    )
