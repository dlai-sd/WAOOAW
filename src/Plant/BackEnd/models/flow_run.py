"""FlowRunModel — tracks execution of a named flow within a hired agent's skill.

Supports a 6-status machine: pending | running | awaiting_approval |
completed | failed | partial_failure.

An idempotency_key unique constraint prevents duplicate executions.
"""

from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

FLOW_RUN_STATUSES = (
    "pending", "running", "awaiting_approval",
    "completed", "failed", "partial_failure"
)


class FlowRunModel(Base):
    """Execution record for a single flow invocation."""

    __tablename__ = "flow_runs"

    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)
    flow_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    current_step = Column(String, nullable=True)
    run_context = Column(JSONB, nullable=False, default=dict)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_flow_runs_hired_instance_id", "hired_instance_id"),
        Index("ix_flow_runs_status", "status"),
        Index("ix_flow_runs_idempotency_key", "idempotency_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<FlowRunModel(id={self.id!r}, hired_instance_id={self.hired_instance_id!r}, "
            f"flow_name={self.flow_name!r}, status={self.status!r})>"
        )
