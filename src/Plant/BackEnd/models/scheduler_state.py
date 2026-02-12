"""Scheduler state model for admin controls.

Tracks scheduler operational state (paused/running) and admin actions.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, JSON, Index
from sqlalchemy.orm import Session

from core.database import Base


class SchedulerStateModel(Base):
    """Model for scheduler operational state."""
    
    __tablename__ = "scheduler_state"
    
    state_id = Column(String, primary_key=True)  # "global" (singleton)
    status = Column(String, nullable=False)  # "running" | "paused"
    paused_at = Column(DateTime(timezone=True))
    paused_by = Column(String)  # Operator who paused
    paused_reason = Column(String)
    resumed_at = Column(DateTime(timezone=True))
    resumed_by = Column(String)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    state_metadata = Column(JSON)  # Additional metadata (renamed from metadata)
    
    __table_args__ = (
        Index("idx_scheduler_state_status", "status"),
        Index("idx_scheduler_state_updated_at", "updated_at"),
    )
    
    @classmethod
    def get_global_state(cls, state_id: str = "global") -> "SchedulerStateModel":
        """Get global scheduler state (singleton pattern).
        
        Args:
            state_id: State ID (default "global")
            
        Returns:
            New SchedulerStateModel with running status
        """
        return cls(
            state_id=state_id,
            status="running",
            updated_at=datetime.now(timezone.utc),
            state_metadata={},
        )
    
    def pause(self, operator: str, reason: Optional[str] = None) -> None:
        """Pause the scheduler.
        
        Args:
            operator: Username/ID of operator pausing scheduler
            reason: Optional reason for pausing
        """
        self.status = "paused"
        self.paused_at = datetime.now(timezone.utc)
        self.paused_by = operator
        self.paused_reason = reason
        self.updated_at = datetime.now(timezone.utc)
    
    def resume(self, operator: str) -> None:
        """Resume the scheduler.
        
        Args:
            operator: Username/ID of operator resuming scheduler
        """
        self.status = "running"
        self.resumed_at = datetime.now(timezone.utc)
        self.resumed_by = operator
        self.updated_at = datetime.now(timezone.utc)
    
    def is_paused(self) -> bool:
        """Check if scheduler is paused.
        
        Returns:
            True if paused, False if running
        """
        return self.status == "paused"
    
    def is_running(self) -> bool:
        """Check if scheduler is running.
        
        Returns:
            True if running, False if paused
        """
        return self.status == "running"
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "state_id": self.state_id,
            "status": self.status,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "paused_by": self.paused_by,
            "paused_reason": self.paused_reason,
            "resumed_at": self.resumed_at.isoformat() if self.resumed_at else None,
            "resumed_by": self.resumed_by,
            "updated_at": self.updated_at.isoformat(),
            "state_metadata": self.state_metadata,
        }


class SchedulerActionLogModel(Base):
    """Model for auditing scheduler admin actions."""
    
    __tablename__ = "scheduler_action_log"
    
    log_id = Column(String, primary_key=True)
    action = Column(String, nullable=False)  # "pause" | "resume" | "trigger"
    operator = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    goal_instance_id = Column(String)  # For manual triggers
    reason = Column(String)
    action_metadata = Column(JSON)  # Renamed from metadata
    
    __table_args__ = (
        Index("idx_scheduler_action_log_timestamp", "timestamp"),
        Index("idx_scheduler_action_log_operator", "operator"),
        Index("idx_scheduler_action_log_action", "action"),
    )
    
    @classmethod
    def create_log(
        cls,
        log_id: str,
        action: str,
        operator: str,
        goal_instance_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "SchedulerActionLogModel":
        """Create action log entry.
        
        Args:
            log_id: Unique log ID
            action: Action type (pause/resume/trigger)
            operator: Username/ID of operator
            goal_instance_id: Goal instance ID (for triggers)
            reason: Optional reason
            metadata: Additional metadata
            
        Returns:
            New SchedulerActionLogModel
        """
        return cls(
            log_id=log_id,
            action=action,
            operator=operator,
            timestamp=datetime.now(timezone.utc),
            goal_instance_id=goal_instance_id,
            reason=reason,
            action_metadata=metadata or {},
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "log_id": self.log_id,
            "action": self.action,
            "operator": self.operator,
            "timestamp": self.timestamp.isoformat(),
            "goal_instance_id": self.goal_instance_id,
            "reason": self.reason,
            "action_metadata": self.action_metadata,
        }


class SchedulerStateRepository:
    """Repository for scheduler state database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_state(self, state_id: str = "global") -> Optional[SchedulerStateModel]:
        """Get scheduler state by ID.
        
        Args:
            state_id: State ID (default "global")
            
        Returns:
            SchedulerStateModel or None if not found
        """
        return self.db.query(SchedulerStateModel).filter(
            SchedulerStateModel.state_id == state_id
        ).first()
    
    def get_or_create_state(self, state_id: str = "global") -> SchedulerStateModel:
        """Get or create scheduler state (singleton).
        
        Args:
            state_id: State ID (default "global")
            
        Returns:
            SchedulerStateModel
        """
        state = self.get_state(state_id)
        if state:
            return state
        
        # Create new state
        state = SchedulerStateModel.get_global_state(state_id)
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state
    
    def update_state(self, state: SchedulerStateModel) -> SchedulerStateModel:
        """Update scheduler state.
        
        Args:
            state: SchedulerStateModel to update
            
        Returns:
            Updated SchedulerStateModel
        """
        self.db.commit()
        self.db.refresh(state)
        return state


class SchedulerActionLogRepository:
    """Repository for scheduler action log database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def add_log(self, log: SchedulerActionLogModel) -> SchedulerActionLogModel:
        """Add action log entry.
        
        Args:
            log: SchedulerActionLogModel to add
            
        Returns:
            Added SchedulerActionLogModel
        """
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_recent_logs(self, limit: int = 100) -> list[SchedulerActionLogModel]:
        """Get recent action logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of SchedulerActionLogModel
        """
        return self.db.query(SchedulerActionLogModel).order_by(
            SchedulerActionLogModel.timestamp.desc()
        ).limit(limit).all()
    
    def get_logs_by_operator(
        self,
        operator: str,
        limit: int = 100,
    ) -> list[SchedulerActionLogModel]:
        """Get logs by operator.
        
        Args:
            operator: Operator username/ID
            limit: Maximum number of logs to return
            
        Returns:
            List of SchedulerActionLogModel
        """
        return self.db.query(SchedulerActionLogModel).filter(
            SchedulerActionLogModel.operator == operator
        ).order_by(
            SchedulerActionLogModel.timestamp.desc()
        ).limit(limit).all()
