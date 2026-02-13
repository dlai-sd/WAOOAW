"""Database models for payments scaffolding.

Minimal models for Phase 1 subscription/payment scaffolding.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Index
from sqlalchemy.orm import relationship

from core.database import Base


class SubscriptionModel(Base):
    """Database model for subscriptions (minimal Phase 1 scaffolding).
    
    Replaces in-memory payments_simple.py _SubscriptionRecord storage.
    """
    
    __tablename__ = "subscriptions"
    
    # Primary key
    subscription_id = Column(String, primary_key=True)
    
    # Subscription details
    agent_id = Column(String, nullable=False, index=True)
    duration = Column(String, nullable=False)  # monthly, quarterly, yearly
    customer_id = Column(String, nullable=True, index=True)
    
    # Status management
    status = Column(String, nullable=False, index=True)  # active, canceled, past_due
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_subscriptions_agent_id", "agent_id"),
        Index("ix_subscriptions_customer_id", "customer_id"),
        Index("ix_subscriptions_status", "status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<SubscriptionModel("
            f"subscription_id={self.subscription_id!r}, "
            f"agent_id={self.agent_id!r}, "
            f"customer_id={self.customer_id!r}, "
            f"status={self.status!r}"
            f")>"
        )
