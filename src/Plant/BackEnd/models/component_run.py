"""ComponentRunModel — tracks execution of a single component step within a FlowRun.

Each record links back to a FlowRun via `flow_run_id` and stores JSONB
`input_context` and `output`, plus `duration_ms` for observability.

Status machine: pending | running | completed | failed
"""

from sqlalchemy import Column, String, DateTime, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

COMPONENT_RUN_STATUSES = ("pending", "running", "completed", "failed")


class ComponentRunModel(Base):
    """Execution record for a single component step within a flow run."""

    __tablename__ = "component_runs"

    id = Column(String, primary_key=True, nullable=False)
    flow_run_id = Column(String, ForeignKey("flow_runs.id"), nullable=False, index=True)
    component_type = Column(String, nullable=False, index=True)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    input_context = Column(JSONB, nullable=False, default=dict)
    output = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_component_runs_flow_run_id", "flow_run_id"),
        Index("ix_component_runs_component_type", "component_type"),
        Index("ix_component_runs_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComponentRunModel(id={self.id!r}, flow_run_id={self.flow_run_id!r}, "
            f"component_type={self.component_type!r}, status={self.status!r})>"
        )
