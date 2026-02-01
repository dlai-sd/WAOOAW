"""
Trial Database Models

Models for managing customer trials of AI agents.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from core.database import Base


class TrialStatus(str, Enum):
    """Trial status enumeration."""
    ACTIVE = "active"
    CONVERTED = "converted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Trial(Base):
    """
    Trial model - represents a customer trial of an AI agent.
    
    Trials are 7-day free trials where customers can:
    - Use agent capabilities fully
    - Keep all deliverables even if cancelled
    - Cancel anytime with no payment
    - Convert to paid subscription after trial
    """
    __tablename__ = "trials"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agent_entity.id"), nullable=False)
    
    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    
    # Trial dates
    start_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default=TrialStatus.ACTIVE.value)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    # Note: Agent model needs to add: trials = relationship("Trial", back_populates="agent")
    deliverables = relationship("TrialDeliverable", back_populates="trial", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize trial with computed end_date if not provided."""
        super().__init__(**kwargs)
        if not self.end_date and self.start_date:
            # Default to 7-day trial
            self.end_date = self.start_date + timedelta(days=7)

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in trial."""
        if self.status != TrialStatus.ACTIVE.value:
            return 0

        if not self.end_date:
            return 0

        now = datetime.now(timezone.utc)
        end_date_utc = self._as_utc(self.end_date)
        if now > end_date_utc:
            return 0

        delta = end_date_utc - now
        return max(0, delta.days)
    
    @property
    def is_expired(self) -> bool:
        """Check if trial has expired."""
        if not self.end_date:
            return False

        now = datetime.now(timezone.utc)
        end_date_utc = self._as_utc(self.end_date)
        return now > end_date_utc and self.status == TrialStatus.ACTIVE.value
    
    def __repr__(self):
        return f"<Trial(id={self.id}, agent_id={self.agent_id}, customer={self.customer_name}, status={self.status})>"


class TrialDeliverable(Base):
    """
    Trial deliverable model - represents files/work produced during trial.
    
    Customers keep these even if they cancel the trial.
    """
    __tablename__ = "trial_deliverables"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id = Column(PG_UUID(as_uuid=True), ForeignKey("trials.id"), nullable=False)
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # S3/GCS path
    file_size = Column(Integer, nullable=True)  # Bytes
    mime_type = Column(String(100), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    trial = relationship("Trial", back_populates="deliverables")
    
    def __repr__(self):
        return f"<TrialDeliverable(id={self.id}, trial_id={self.trial_id}, file={self.file_name})>"
