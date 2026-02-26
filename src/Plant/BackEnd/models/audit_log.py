"""AuditLog model — Iteration 2, E1-S2.

SQLAlchemy model for the audit_logs table. Audit records are append-only;
they are soft-deleted (deleted_at set) never hard-deleted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import declarative_base

# Use the same declarative base as the rest of the app.
from core.database import Base


class AuditLog(Base):
    """Single audit event record."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('success', 'failure')",
            name="ck_audit_logs_outcome",
        ),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # User identity
    user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    email = Column(Text, nullable=True)

    # Request context
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Event classification
    screen = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    outcome = Column(Text, nullable=False)  # 'success' | 'failure'

    # Detail + metadata
    detail = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True, default=dict)

    # Tracing
    correlation_id = Column(Text, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
