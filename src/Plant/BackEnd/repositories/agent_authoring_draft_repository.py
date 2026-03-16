"""Repository for Plant-owned agent authoring draft lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_authoring_draft import AgentAuthoringDraftModel


class AgentAuthoringDraftRepository:
    """Persistence operations for PP-authored base contract drafts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_drafts(self, status: str | None = None) -> list[AgentAuthoringDraftModel]:
        stmt = select(AgentAuthoringDraftModel).order_by(
            desc(AgentAuthoringDraftModel.updated_at),
            desc(AgentAuthoringDraftModel.created_at),
        )
        if status is not None:
            stmt = stmt.where(AgentAuthoringDraftModel.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, draft_id: str) -> AgentAuthoringDraftModel | None:
        stmt = select(AgentAuthoringDraftModel).where(
            AgentAuthoringDraftModel.draft_id == draft_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_draft(
        self,
        *,
        draft_id: str | None,
        candidate_agent_type_id: str,
        candidate_agent_label: str,
        contract_payload: dict[str, Any],
        section_states: dict[str, str],
        constraint_policy: dict[str, Any],
    ) -> AgentAuthoringDraftModel:
        draft = await self.get_by_id(draft_id) if draft_id else None
        now = datetime.now(timezone.utc)

        if draft is None:
            draft = AgentAuthoringDraftModel(
                draft_id=draft_id or f"AAD-{uuid4()}",
                candidate_agent_type_id=candidate_agent_type_id,
                candidate_agent_label=candidate_agent_label,
                contract_payload=contract_payload,
                section_states=section_states,
                constraint_policy=constraint_policy,
                status="draft",
                created_at=now,
                updated_at=now,
            )
            self.session.add(draft)
        else:
            draft.candidate_agent_type_id = candidate_agent_type_id
            draft.candidate_agent_label = candidate_agent_label
            draft.contract_payload = dict(contract_payload)
            draft.section_states = dict(section_states)
            draft.constraint_policy = dict(constraint_policy)
            draft.updated_at = now

        await self.session.flush()
        await self.session.refresh(draft)
        return draft

    async def submit_for_review(self, draft_id: str) -> AgentAuthoringDraftModel | None:
        draft = await self.get_by_id(draft_id)
        if draft is None:
            return None
        if draft.status not in {"draft", "changes_requested"}:
            raise ValueError(f"Draft {draft_id} cannot be submitted from status {draft.status}")

        now = datetime.now(timezone.utc)
        draft.status = "in_review"
        draft.submitted_at = now
        draft.updated_at = now
        await self.session.flush()
        await self.session.refresh(draft)
        return draft

    async def request_changes(
        self,
        draft_id: str,
        *,
        reviewer_comments: list[dict[str, Any]],
        reviewer_id: str | None,
        reviewer_name: str | None,
    ) -> AgentAuthoringDraftModel | None:
        draft = await self.get_by_id(draft_id)
        if draft is None:
            return None
        if draft.status != "in_review":
            raise ValueError(f"Draft {draft_id} cannot request changes from status {draft.status}")

        now = datetime.now(timezone.utc)
        draft.status = "changes_requested"
        draft.reviewer_comments = list(reviewer_comments)
        draft.reviewer_id = reviewer_id
        draft.reviewer_name = reviewer_name
        draft.reviewed_at = now
        draft.updated_at = now
        await self.session.flush()
        await self.session.refresh(draft)
        return draft

    async def approve(
        self,
        draft_id: str,
        *,
        reviewer_id: str | None,
        reviewer_name: str | None,
    ) -> AgentAuthoringDraftModel | None:
        draft = await self.get_by_id(draft_id)
        if draft is None:
            return None
        if draft.status != "in_review":
            raise ValueError(f"Draft {draft_id} cannot be approved from status {draft.status}")

        now = datetime.now(timezone.utc)
        draft.status = "approved"
        draft.reviewer_id = reviewer_id
        draft.reviewer_name = reviewer_name
        draft.reviewed_at = now
        draft.updated_at = now
        await self.session.flush()
        await self.session.refresh(draft)
        return draft

    async def patch_constraint_policy(
        self,
        draft_id: str,
        *,
        constraint_policy: dict[str, Any],
    ) -> AgentAuthoringDraftModel | None:
        draft = await self.get_by_id(draft_id)
        if draft is None:
            return None

        draft.constraint_policy = dict(constraint_policy)
        draft.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(draft)
        return draft