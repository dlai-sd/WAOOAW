"""Plant-owned persistence model for PP base agent contract drafts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class AgentAuthoringDraftModel(Base):
    """Persisted PP authoring draft that can be reopened across review cycles."""

    __tablename__ = "agent_authoring_drafts"

    draft_id = Column(String, primary_key=True, nullable=False)
    candidate_agent_type_id = Column(String, nullable=False)
    candidate_agent_label = Column(String, nullable=False)

    contract_payload = Column(JSONB, nullable=False, default=dict)
    section_states = Column(JSONB, nullable=False, default=dict)
    constraint_policy = Column(JSONB, nullable=False, default=dict)
    reviewer_comments = Column(JSONB, nullable=False, default=list)

    status = Column(String, nullable=False, default="draft")
    reviewer_id = Column(String, nullable=True)
    reviewer_name = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_agent_authoring_drafts_candidate_agent_type_id",
            "candidate_agent_type_id",
        ),
        Index("ix_agent_authoring_drafts_status", "status"),
    )

    def __init__(
        self,
        *,
        draft_id: str,
        candidate_agent_type_id: str,
        candidate_agent_label: str,
        contract_payload: dict[str, Any] | None = None,
        section_states: dict[str, str] | None = None,
        constraint_policy: dict[str, Any] | None = None,
        reviewer_comments: list[dict[str, Any]] | None = None,
        status: str = "draft",
        reviewer_id: str | None = None,
        reviewer_name: str | None = None,
        submitted_at: datetime | None = None,
        reviewed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.draft_id = draft_id
        self.candidate_agent_type_id = candidate_agent_type_id
        self.candidate_agent_label = candidate_agent_label
        self.contract_payload = dict(contract_payload or {})
        self.section_states = dict(section_states or {})
        self.constraint_policy = dict(constraint_policy or {})
        self.reviewer_comments = list(reviewer_comments or [])
        self.status = status
        self.reviewer_id = reviewer_id
        self.reviewer_name = reviewer_name
        self.submitted_at = submitted_at
        self.reviewed_at = reviewed_at
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now