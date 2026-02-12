"""Dead letter queue model for persistently failed scheduler goals.

This model stores goals that have been retried the maximum number of times
and require manual intervention. Items expire after 7 days.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, Index
from sqlalchemy.orm import Session
from core.database import Base


class SchedulerDLQModel(Base):
    """Dead letter queue for failed goal executions."""
    
    __tablename__ = "scheduler_dlq"
    
    dlq_id = Column(String, primary_key=True)
    goal_instance_id = Column(String, nullable=False, index=True)
    hired_instance_id = Column(String, nullable=False, index=True)
    error_type = Column(String)  # TRANSIENT or PERMANENT
    error_message = Column(Text)
    stack_trace = Column(Text)
    failure_count = Column(Integer, default=1)
    first_failed_at = Column(DateTime(timezone=True), nullable=False)
    last_failed_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    retry_count = Column(Integer, default=0)  # Track manual retry attempts
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_scheduler_dlq_expires_at", "expires_at"),
        Index("idx_scheduler_dlq_goal_instance_id", "goal_instance_id"),
    )
    
    @classmethod
    def create_from_failure(
        cls,
        dlq_id: str,
        goal_instance_id: str,
        hired_instance_id: str,
        error_type: str,
        error_message: str,
        stack_trace: str | None,
        failure_count: int,
    ) -> "SchedulerDLQModel":
        """Create a new DLQ entry from a failed goal execution.
        
        Args:
            dlq_id: Unique identifier for the DLQ entry
            goal_instance_id: ID of the goal instance that failed
            hired_instance_id: ID of the hired agent instance
            error_type: Type of error (TRANSIENT or PERMANENT)
            error_message: Human-readable error message
            stack_trace: Full stack trace (optional)
            failure_count: Number of times goal execution was attempted
            
        Returns:
            New SchedulerDLQModel instance
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)
        
        return cls(
            dlq_id=dlq_id,
            goal_instance_id=goal_instance_id,
            hired_instance_id=hired_instance_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            failure_count=failure_count,
            first_failed_at=now,
            last_failed_at=now,
            expires_at=expires_at,
            retry_count=0,
        )
    
    def update_failure(self, error_message: str, stack_trace: str | None) -> None:
        """Update failure details for an existing DLQ entry.
        
        Args:
            error_message: New error message
            stack_trace: New stack trace (optional)
        """
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.failure_count += 1
        self.last_failed_at = datetime.now(timezone.utc)
    
    def record_retry_attempt(self) -> None:
        """Record that a manual retry was attempted."""
        self.retry_count += 1
    
    def is_expired(self) -> bool:
        """Check if this DLQ entry has expired.
        
        Returns:
            True if entry is past expiration date
        """
        return datetime.now(timezone.utc) >= self.expires_at


class SchedulerDLQRepository:
    """Repository for DLQ database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def add(self, dlq_entry: SchedulerDLQModel) -> SchedulerDLQModel:
        """Add a new DLQ entry to the database.
        
        Args:
            dlq_entry: DLQ entry to add
            
        Returns:
            The added entry
        """
        self.db.add(dlq_entry)
        self.db.commit()
        self.db.refresh(dlq_entry)
        return dlq_entry
    
    def get_by_id(self, dlq_id: str) -> SchedulerDLQModel | None:
        """Get a DLQ entry by ID.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            DLQ entry or None if not found
        """
        return self.db.query(SchedulerDLQModel).filter(
            SchedulerDLQModel.dlq_id == dlq_id
        ).first()
    
    def get_by_goal_instance(self, goal_instance_id: str) -> SchedulerDLQModel | None:
        """Get a DLQ entry by goal instance ID.
        
        Args:
            goal_instance_id: Goal instance ID
            
        Returns:
            DLQ entry or None if not found
        """
        return self.db.query(SchedulerDLQModel).filter(
            SchedulerDLQModel.goal_instance_id == goal_instance_id
        ).first()
    
    def list_active(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SchedulerDLQModel]:
        """List active (non-expired) DLQ entries.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of active DLQ entries
        """
        now = datetime.now(timezone.utc)
        return (
            self.db.query(SchedulerDLQModel)
            .filter(SchedulerDLQModel.expires_at > now)
            .order_by(SchedulerDLQModel.last_failed_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def count_active(self) -> int:
        """Count active (non-expired) DLQ entries.
        
        Returns:
            Number of active DLQ entries
        """
        now = datetime.now(timezone.utc)
        return (
            self.db.query(SchedulerDLQModel)
            .filter(SchedulerDLQModel.expires_at > now)
            .count()
        )
    
    def delete_expired(self) -> int:
        """Delete expired DLQ entries.
        
        Returns:
            Number of entries deleted
        """
        now = datetime.now(timezone.utc)
        deleted_count = (
            self.db.query(SchedulerDLQModel)
            .filter(SchedulerDLQModel.expires_at <= now)
            .delete()
        )
        self.db.commit()
        return deleted_count
    
    def update(self, dlq_entry: SchedulerDLQModel) -> SchedulerDLQModel:
        """Update an existing DLQ entry.
        
        Args:
            dlq_entry: DLQ entry with updated fields
            
        Returns:
            Updated entry
        """
        self.db.commit()
        self.db.refresh(dlq_entry)
        return dlq_entry
    
    def delete(self, dlq_id: str) -> bool:
        """Delete a DLQ entry by ID.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            True if deleted, False if not found
        """
        deleted_count = (
            self.db.query(SchedulerDLQModel)
            .filter(SchedulerDLQModel.dlq_id == dlq_id)
            .delete()
        )
        self.db.commit()
        return deleted_count > 0
