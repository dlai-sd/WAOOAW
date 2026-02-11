"""HiredAgent and GoalInstance DB models for persisting agent instances and goals.

Replaces in-memory storage from hired_agents_simple.py with durable DB persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


TrialStatus = Literal["not_started", "active", "ended_converted", "ended_not_converted"]


class HiredAgentModel(Base):
    """Hired agent instance table.
    
    Tracks customer-owned agent instances tied to subscriptions.
    Each instance has configuration, goals, and trial lifecycle state.
    """
    
    __tablename__ = "hired_agents"
    
    # Primary key
    hired_instance_id = Column(String, primary_key=True, nullable=False)
    
    # Core identifiers
    subscription_id = Column(String, nullable=False, unique=True, index=True)
    agent_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=True, index=True)  # Nullable during draft phase
    
    # Configuration
    nickname = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    config = Column(JSONB, nullable=False, default={})
    
    # State flags
    configured = Column(Boolean, nullable=False, default=False)
    goals_completed = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    
    # Trial lifecycle
    trial_status = Column(String, nullable=False, default="not_started")
    trial_start_at = Column(DateTime(timezone=True), nullable=True)
    trial_end_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    goals = relationship("GoalInstanceModel", back_populates="hired_agent", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_hired_agents_subscription_id", "subscription_id"),
        Index("ix_hired_agents_agent_id", "agent_id"),
        Index("ix_hired_agents_customer_id", "customer_id"),
        Index("ix_hired_agents_trial_status", "trial_status"),
    )
    
    def __init__(
        self,
        hired_instance_id: str,
        subscription_id: str,
        agent_id: str,
        customer_id: str | None = None,
        nickname: str | None = None,
        theme: str | None = None,
        config: dict[str, Any] | None = None,
        configured: bool = False,
        goals_completed: bool = False,
        active: bool = True,
        trial_status: str = "not_started",
        trial_start_at: datetime | None = None,
        trial_end_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize HiredAgentModel."""
        self.hired_instance_id = hired_instance_id
        self.subscription_id = subscription_id
        self.agent_id = agent_id
        self.customer_id = customer_id
        self.nickname = nickname
        self.theme = theme
        self.config = config or {}
        self.configured = configured
        self.goals_completed = goals_completed
        self.active = active
        self.trial_status = trial_status
        self.trial_start_at = trial_start_at
        self.trial_end_at = trial_end_at
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
    
    def __repr__(self) -> str:
        return (
            f"<HiredAgentModel(hired_instance_id={self.hired_instance_id!r}, "
            f"subscription_id={self.subscription_id!r}, agent_id={self.agent_id!r})>"
        )


class GoalInstanceModel(Base):
    """Goal instance table.
    
    Tracks goals associated with hired agent instances.
    Each goal is defined by a goal template and has customer settings.
    """
    
    __tablename__ = "goal_instances"
    
    # Primary key
    goal_instance_id = Column(String, primary_key=True, nullable=False)
    
    # Foreign key to hired agent
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Goal definition
    goal_template_id = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    settings = Column(JSONB, nullable=False, default={})
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    hired_agent = relationship("HiredAgentModel", back_populates="goals")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("goal_instance_id", name="uq_goal_instance_id"),
        Index("ix_goal_instances_hired_instance_id", "hired_instance_id"),
    )
    
    def __init__(
        self,
        goal_instance_id: str,
        hired_instance_id: str,
        goal_template_id: str,
        frequency: str,
        settings: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize GoalInstanceModel."""
        self.goal_instance_id = goal_instance_id
        self.hired_instance_id = hired_instance_id
        self.goal_template_id = goal_template_id
        self.frequency = frequency
        self.settings = settings or {}
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
    
    def __repr__(self) -> str:
        return (
            f"<GoalInstanceModel(goal_instance_id={self.goal_instance_id!r}, "
            f"hired_instance_id={self.hired_instance_id!r}, "
            f"goal_template_id={self.goal_template_id!r})>"
        )
