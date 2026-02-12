"""Goal run model for tracking individual goal executions with idempotency.

This model ensures each goal run is executed exactly once by tracking
runs with unique idempotency keys and preventing duplicate executions.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Index, text
from sqlalchemy.orm import Session
from core.database import Base


class GoalRunModel(Base):
    """Track individual goal runs with idempotency guarantees."""
    
    __tablename__ = "goal_runs"
    
    run_id = Column(String, primary_key=True)
    goal_instance_id = Column(String, nullable=False, index=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False)  # pending | running | completed | failed
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    deliverable_id = Column(String)
    error_details = Column(JSON)
    duration_ms = Column(JSON)  # Execution duration in milliseconds
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_goal_runs_idempotency_key", "idempotency_key"),
        Index("idx_goal_runs_goal_instance_id", "goal_instance_id"),
        Index("idx_goal_runs_status", "status"),
    )
    
    @classmethod
    def create_pending(
        cls,
        run_id: str,
        goal_instance_id: str,
        idempotency_key: str,
    ) -> "GoalRunModel":
        """Create a new pending goal run.
        
        Args:
            run_id: Unique identifier for this run
            goal_instance_id: ID of the goal instance
            idempotency_key: Unique key to prevent duplicate runs
            
        Returns:
            New GoalRunModel in pending status
        """
        return cls(
            run_id=run_id,
            goal_instance_id=goal_instance_id,
            idempotency_key=idempotency_key,
            status="pending",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            deliverable_id=None,
            error_details=None,
            duration_ms=None,
        )
    
    def mark_running(self) -> None:
        """Mark run as currently running."""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
    
    def mark_completed(self, deliverable_id: str, duration_ms: int) -> None:
        """Mark run as completed successfully.
        
        Args:
            deliverable_id: ID of the created deliverable
            duration_ms: Execution duration in milliseconds
        """
        self.status = "completed"
        self.deliverable_id = deliverable_id
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = duration_ms
        self.error_details = None
    
    def mark_failed(self, error_details: dict, duration_ms: int) -> None:
        """Mark run as failed.
        
        Args:
            error_details: Error information (message, type, stack trace)
            duration_ms: Execution duration in milliseconds
        """
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = duration_ms
        self.error_details = error_details
    
    def is_terminal_state(self) -> bool:
        """Check if run is in a terminal state (completed or failed).
        
        Returns:
            True if run is completed or failed
        """
        return self.status in ("completed", "failed")
    
    def to_dict(self) -> dict:
        """Convert run to dictionary representation.
        
        Returns:
            Dictionary with run details
        """
        return {
            "run_id": self.run_id,
            "goal_instance_id": self.goal_instance_id,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deliverable_id": self.deliverable_id,
            "error_details": self.error_details,
            "duration_ms": self.duration_ms,
        }


class GoalRunRepository:
    """Repository for goal run database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_idempotency_key(self, idempotency_key: str) -> GoalRunModel | None:
        """Get a run by its idempotency key.
        
        Args:
            idempotency_key: Idempotency key to search for
            
        Returns:
            GoalRunModel or None if not found
        """
        return self.db.query(GoalRunModel).filter(
            GoalRunModel.idempotency_key == idempotency_key
        ).first()
    
    def get_by_run_id(self, run_id: str) -> GoalRunModel | None:
        """Get a run by its run ID.
        
        Args:
            run_id: Run ID to search for
            
        Returns:
            GoalRunModel or None if not found
        """
        return self.db.query(GoalRunModel).filter(
            GoalRunModel.run_id == run_id
        ).first()
    
    def create_with_lock(self, goal_run: GoalRunModel) -> GoalRunModel:
        """Create a new goal run with database lock to prevent concurrent creation.
        
        Uses SELECT FOR UPDATE to acquire row-level lock and prevent
        race conditions when creating runs with same idempotency key.
        
        Args:
            goal_run: GoalRunModel to create
            
        Returns:
            Created GoalRunModel
            
        Raises:
            IntegrityError: If run with same idempotency key already exists
        """
        # Try to acquire lock on any existing run with this key
        existing = self.db.query(GoalRunModel).filter(
            GoalRunModel.idempotency_key == goal_run.idempotency_key
        ).with_for_update(nowait=False).first()
        
        if existing:
            # Run already exists, return it
            return existing
        
        # No existing run, create new one
        self.db.add(goal_run)
        self.db.commit()
        self.db.refresh(goal_run)
        return goal_run
    
    def update(self, goal_run: GoalRunModel) -> GoalRunModel:
        """Update an existing goal run.
        
        Args:
            goal_run: GoalRunModel with updated fields
            
        Returns:
            Updated GoalRunModel
        """
        self.db.commit()
        self.db.refresh(goal_run)
        return goal_run
    
    def list_by_goal_instance(
        self,
        goal_instance_id: str,
        limit: int = 100,
    ) -> list[GoalRunModel]:
        """List runs for a specific goal instance.
        
        Args:
            goal_instance_id: Goal instance ID
            limit: Maximum number of runs to return
            
        Returns:
            List of GoalRunModel ordered by started_at descending
        """
        return (
            self.db.query(GoalRunModel)
            .filter(GoalRunModel.goal_instance_id == goal_instance_id)
            .order_by(GoalRunModel.started_at.desc())
            .limit(limit)
            .all()
        )
    
    def list_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> list[GoalRunModel]:
        """List runs with a specific status.
        
        Args:
            status: Run status (pending, running, completed, failed)
            limit: Maximum number of runs to return
            
        Returns:
            List of GoalRunModel ordered by started_at descending
        """
        return (
            self.db.query(GoalRunModel)
            .filter(GoalRunModel.status == status)
            .order_by(GoalRunModel.started_at.desc())
            .limit(limit)
            .all()
        )
