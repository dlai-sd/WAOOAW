"""Plant routes for PP base agent contract authoring drafts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.routing import waooaw_router
from models.agent_authoring_draft import AgentAuthoringDraftModel
from repositories.agent_authoring_draft_repository import AgentAuthoringDraftRepository


DraftStatus = Literal["draft", "in_review", "changes_requested", "approved"]
SectionState = Literal["missing", "ready", "needs_review"]

router = waooaw_router(prefix="/agent-authoring", tags=["agent-authoring"])


class ReviewerComment(BaseModel):
    section_key: str = Field(min_length=1)
    comment: str = Field(min_length=1)
    severity: Literal["info", "changes_requested"] = "changes_requested"
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    created_at: datetime | None = None


class SaveDraftRequest(BaseModel):
    draft_id: str | None = None
    candidate_agent_type_id: str = Field(min_length=1)
    candidate_agent_label: str = Field(min_length=1)
    contract_payload: dict[str, Any] = Field(default_factory=dict)
    section_states: dict[str, SectionState] = Field(default_factory=dict)
    constraint_policy: dict[str, Any] = Field(default_factory=dict)


class ReviewActionRequest(BaseModel):
    reviewer_id: str | None = None
    reviewer_name: str | None = None


class ChangesRequestedRequest(ReviewActionRequest):
    reviewer_comments: list[ReviewerComment] = Field(min_length=1)


class ConstraintPolicyPatchRequest(BaseModel):
    constraint_policy: dict[str, Any] = Field(default_factory=dict)


class AgentAuthoringDraftResponse(BaseModel):
    draft_id: str
    candidate_agent_type_id: str
    candidate_agent_label: str
    contract_payload: dict[str, Any]
    section_states: dict[str, SectionState]
    constraint_policy: dict[str, Any]
    reviewer_comments: list[ReviewerComment]
    status: DraftStatus
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


def get_read_repository(
    session: AsyncSession = Depends(get_read_db_session),
) -> AgentAuthoringDraftRepository:
    return AgentAuthoringDraftRepository(session)


def get_write_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AgentAuthoringDraftRepository:
    return AgentAuthoringDraftRepository(session)


def _to_response(draft: AgentAuthoringDraftModel) -> AgentAuthoringDraftResponse:
    return AgentAuthoringDraftResponse(
        draft_id=draft.draft_id,
        candidate_agent_type_id=draft.candidate_agent_type_id,
        candidate_agent_label=draft.candidate_agent_label,
        contract_payload=dict(draft.contract_payload or {}),
        section_states=dict(draft.section_states or {}),
        constraint_policy=dict(draft.constraint_policy or {}),
        reviewer_comments=[
            ReviewerComment(**comment) for comment in list(draft.reviewer_comments or [])
        ],
        status=draft.status,
        reviewer_id=draft.reviewer_id,
        reviewer_name=draft.reviewer_name,
        submitted_at=draft.submitted_at,
        reviewed_at=draft.reviewed_at,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.get("/drafts", response_model=list[AgentAuthoringDraftResponse])
async def list_drafts(
    status: DraftStatus | None = None,
    repository: AgentAuthoringDraftRepository = Depends(get_read_repository),
) -> list[AgentAuthoringDraftResponse]:
    drafts = await repository.list_drafts(status=status)
    return [_to_response(draft) for draft in drafts]


@router.get("/drafts/{draft_id}", response_model=AgentAuthoringDraftResponse)
async def get_draft(
    draft_id: str,
    repository: AgentAuthoringDraftRepository = Depends(get_read_repository),
) -> AgentAuthoringDraftResponse:
    draft = await repository.get_by_id(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return _to_response(draft)


@router.post("/drafts", response_model=AgentAuthoringDraftResponse)
async def save_draft(
    request: SaveDraftRequest,
    repository: AgentAuthoringDraftRepository = Depends(get_write_repository),
) -> AgentAuthoringDraftResponse:
    draft = await repository.save_draft(**request.model_dump())
    await repository.session.commit()
    return _to_response(draft)


@router.post("/drafts/{draft_id}/submit", response_model=AgentAuthoringDraftResponse)
async def submit_draft(
    draft_id: str,
    repository: AgentAuthoringDraftRepository = Depends(get_write_repository),
) -> AgentAuthoringDraftResponse:
    try:
        draft = await repository.submit_for_review(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    await repository.session.commit()
    return _to_response(draft)


@router.post(
    "/drafts/{draft_id}/changes-requested",
    response_model=AgentAuthoringDraftResponse,
)
async def request_changes(
    draft_id: str,
    request: ChangesRequestedRequest,
    repository: AgentAuthoringDraftRepository = Depends(get_write_repository),
) -> AgentAuthoringDraftResponse:
    try:
        draft = await repository.request_changes(
            draft_id,
            reviewer_comments=[comment.model_dump() for comment in request.reviewer_comments],
            reviewer_id=request.reviewer_id,
            reviewer_name=request.reviewer_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    await repository.session.commit()
    return _to_response(draft)


@router.post("/drafts/{draft_id}/approve", response_model=AgentAuthoringDraftResponse)
async def approve_draft(
    draft_id: str,
    request: ReviewActionRequest,
    repository: AgentAuthoringDraftRepository = Depends(get_write_repository),
) -> AgentAuthoringDraftResponse:
    try:
        draft = await repository.approve(
            draft_id,
            reviewer_id=request.reviewer_id,
            reviewer_name=request.reviewer_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    await repository.session.commit()
    return _to_response(draft)


@router.patch(
    "/drafts/{draft_id}/constraint-policy",
    response_model=AgentAuthoringDraftResponse,
)
async def patch_constraint_policy(
    draft_id: str,
    request: ConstraintPolicyPatchRequest,
    repository: AgentAuthoringDraftRepository = Depends(get_write_repository),
) -> AgentAuthoringDraftResponse:
    draft = await repository.patch_constraint_policy(
        draft_id,
        constraint_policy=request.constraint_policy,
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    await repository.session.commit()
    return _to_response(draft)