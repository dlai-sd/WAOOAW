"""Scheduler persistence model for state recovery.

Tracks scheduled goal runs for recovery after restart.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.orm import Session

from core.database import Base


class ScheduledGoalRunModel(Base):
    """Model for scheduled goal runs."""
    
    __tablename__ = "scheduled_goal_runs"
    
    scheduled_run_id = Column(String, primary_key=True)
    goal_instance_id = Column(String, nullable=False, index=True)
    hired_instance_id = Column(String)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)  # "pending" | "completed" | "cancelled"
    completed_at = Column(DateTime(timezone=True))
    run_metadata = Column(JSON)  # Additional metadata
    
    __table_args__ = (
        Index("idx_scheduled_runs_status", "status"),
        Index("idx_scheduled_runs_goal_time", "goal_instance_id", "scheduled_time"),
    )
    
    @classmethod
    def create_scheduled_run(
        cls,
        scheduled_run_id: str,
        goal_instance_id: str,
        scheduled_time: datetime,
        hired_instance_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "ScheduledGoalRunModel":
        """Create a new scheduled run.
        
        Args:
            scheduled_run_id: Unique ID for this scheduled run
            goal_instance_id: Goal instance ID
            scheduled_time: When to execute (UTC)
            hired_instance_id: Optional hired instance ID
            metadata: Additional metadata
            
        Returns:
            New ScheduledGoalRunModel
        """
        return cls(
            scheduled_run_id=scheduled_run_id,
            goal_instance_id=goal_instance_id,
            hired_instance_id=hired_instance_id,
            scheduled_time=scheduled_time,
            created_at=datetime.now(timezone.utc),
            status="pending",
            run_metadata=metadata or {},
        )
    
    def mark_completed(self) -> None:
        """Mark scheduled run as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_cancelled(self) -> None:
        """Mark scheduled run as cancelled."""
        self.status = "cancelled"
        self.completed_at = datetime.now(timezone.utc)
    
    def is_pending(self) -> bool:
        """Check if run is pending.
        
        Returns:
            True if pending, False otherwise
        """
        return self.status == "pending"
    
    def is_missed(self, current_time: Optional[datetime] = None) -> bool:
        """Check if scheduled run was missed.
        
        Args:
            current_time: Current time (default: now)
            
        Returns:
            True if scheduled time is in the past and still pending
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        return self.is_pending() and self.scheduled_time < current_time
    
    def is_very_old_missed(
        self,
        threshold_hours: int = 24,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """Check if missed run is too old to replay.
        
        Args:
            threshold_hours: Hours past which run is considered too old
            current_time: Current time (default: now)
            
        Returns:
            True if missed and older than threshold
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        if not self.is_missed(current_time):
            return False
        
        threshold = timedelta(hours=threshold_hours)
        return (current_time - self.scheduled_time) > threshold
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "scheduled_run_id": self.scheduled_run_id,
            "goal_instance_id": self.goal_instance_id,
            "hired_instance_id": self.hired_instance_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "run_metadata": self.run_metadata,
        }


class ScheduledGoalRunRepository:
    """Repository for scheduled goal run database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def add(self, scheduled_run: ScheduledGoalRunModel) -> ScheduledGoalRunModel:
        """Add scheduled run to database.
        
        Args:
            scheduled_run: ScheduledGoalRunModel to add
            
        Returns:
            Added ScheduledGoalRunModel
        """
        self.db.add(scheduled_run)
        self.db.commit()
        self.db.refresh(scheduled_run)
        return scheduled_run
    
    def get_by_id(self, scheduled_run_id: str) -> Optional[ScheduledGoalRunModel]:
        """Get scheduled run by ID.
        
        Args:
            scheduled_run_id: Scheduled run ID
            
        Returns:
            ScheduledGoalRunModel or None
        """
        return self.db.query(ScheduledGoalRunModel).filter(
            ScheduledGoalRunModel.scheduled_run_id == scheduled_run_id
        ).first()
    
    def update(self, scheduled_run: ScheduledGoalRunModel) -> ScheduledGoalRunModel:
        """Update scheduled run.
        
        Args:
            scheduled_run: ScheduledGoalRunModel to update
            
        Returns:
            Updated ScheduledGoalRunModel
        """
        self.db.commit()
        self.db.refresh(scheduled_run)
        return scheduled_run
    
    def get_pending_runs(self) -> list[ScheduledGoalRunModel]:
        """Get all pending scheduled runs.
        
        Returns:
            List of pending ScheduledGoalRunModel
        """
        return self.db.query(ScheduledGoalRunModel).filter(
            ScheduledGoalRunModel.status == "pending"
        ).order_by(
            ScheduledGoalRunModel.scheduled_time
        ).all()
    
    def get_missed_runs(
        self,
        current_time: Optional[datetime] = None,
    ) -> list[ScheduledGoalRunModel]:
        """Get all missed scheduled runs.
        
        Args:
            current_time: Current time (default: now)
            
        Returns:
            List of missed ScheduledGoalRunModel
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        return self.db.query(ScheduledGoalRunModel).filter(
            ScheduledGoalRunModel.status == "pending",
            ScheduledGoalRunModel.scheduled_time < current_time,
        ).order_by(
            ScheduledGoalRunModel.scheduled_time
        ).all()
    
    def get_upcoming_runs(
        self,
        limit: int = 100,
        current_time: Optional[datetime] = None,
    ) -> list[ScheduledGoalRunModel]:
        """Get upcoming scheduled runs.
        
        Args:
            limit: Maximum number of runs to return
            current_time: Current time (default: now)
            
        Returns:
            List of upcoming ScheduledGoalRunModel
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        return self.db.query(ScheduledGoalRunModel).filter(
            ScheduledGoalRunModel.status == "pending",
            ScheduledGoalRunModel.scheduled_time >= current_time,
        ).order_by(
            ScheduledGoalRunModel.scheduled_time
        ).limit(limit).all()
    
    def delete_old_completed(
        self,
        days_old: int = 30,
        current_time: Optional[datetime] = None,
    ) -> int:
        """Delete old completed scheduled runs.
        
        Args:
            days_old: Days old to delete
            current_time: Current time (default: now)
            
        Returns:
            Number of rows deleted
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        threshold = current_time - timedelta(days=days_old)
        
        result = self.db.query(ScheduledGoalRunModel).filter(
            ScheduledGoalRunModel.status.in_(["completed", "cancelled"]),
            ScheduledGoalRunModel.completed_at < threshold,
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return result
