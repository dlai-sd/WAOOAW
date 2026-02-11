"""Database models for deliverables and approvals.

Models for Phase 1 deliverables (agent-generated drafts) and approval audit trail.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from core.database import Base


class DeliverableModel(Base):
    """Database model for deliverables (agent-generated drafts for review/execution).
    
    Replaces in-memory deliverables_simple.py storage.
    """
    
    __tablename__ = "deliverables"
    
    # Primary key
    deliverable_id = Column(String, primary_key=True)
    
    # Foreign keys
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_instance_id = Column(
        String,
        ForeignKey("goal_instances.goal_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Deliverable metadata
    goal_template_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)  # JSONB in PostgreSQL
    
    # Review state
    review_status = Column(
        String,
        nullable=False,
        default="pending_review",
        index=True,
    )  # pending_review, approved, rejected
    review_notes = Column(Text, nullable=True)
    approval_id = Column(
        String,
        ForeignKey("approvals.approval_id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Execution state
    execution_status = Column(
        String,
        nullable=False,
        default="not_executed",
    )  # not_executed, executed
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    hired_agent = relationship("HiredAgentModel", back_populates="deliverables")
    goal_instance = relationship("GoalInstanceModel", back_populates="deliverables")
    approval = relationship("ApprovalModel", back_populates="deliverable")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_deliverables_hired_instance_created", "hired_instance_id", "created_at"),
        Index("ix_deliverables_goal_instance", "goal_instance_id"),
        Index("ix_deliverables_review_status", "review_status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DeliverableModel("
            f"deliverable_id={self.deliverable_id!r}, "
            f"title={self.title!r}, "
            f"review_status={self.review_status!r}, "
            f"execution_status={self.execution_status!r}"
            f")>"
        )


class ApprovalModel(Base):
    """Database model for approval audit trail (immutable after creation).
    
    Tracks customer approve/reject decisions for deliverables.
    """
    
    __tablename__ = "approvals"
    
    # Primary key
    approval_id = Column(String, primary_key=True)
    
    # Foreign keys
    deliverable_id = Column(
        String,
        ForeignKey("deliverables.deliverable_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Approval metadata
    customer_id = Column(String, nullable=False, index=True)
    decision = Column(String, nullable=False)  # approved, rejected
    notes = Column(Text, nullable=True)
    
    # Immutable timestamp (no updated_at)
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    deliverable = relationship("DeliverableModel", back_populates="approval")
    
    # Indexes
    __table_args__ = (
        Index("ix_approvals_deliverable", "deliverable_id"),
        Index("ix_approvals_customer", "customer_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ApprovalModel("
            f"approval_id={self.approval_id!r}, "
            f"deliverable_id={self.deliverable_id!r}, "
            f"customer_id={self.customer_id!r}, "
            f"decision={self.decision!r}"
            f")>"
        )
