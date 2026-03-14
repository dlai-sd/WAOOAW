"""PP thin-proxy routes for Plant-owned base agent contract drafts."""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import (
    EntityNotFoundError,
    PlantAPIClient,
    PlantAPIError,
    ValidationError,
    get_plant_client,
)
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger


SectionState = Literal["missing", "ready", "needs_review"]

router = waooaw_router(prefix="/agent-authoring", tags=["agent-authoring"])


class ReviewerComment(BaseModel):
    section_key: str = Field(min_length=1)
    comment: str = Field(min_length=1)
    severity: Literal["info", "changes_requested"] = "changes_requested"
    reviewer_id: str | None = None
    reviewer_name: str | None = None


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


def _correlation_id_from_request(request: Request) -> Optional[str]:
    return request.headers.get("x-correlation-id") or request.headers.get("X-Correlation-ID")


@router.get("/drafts", response_model=list[dict[str, Any]])
async def list_drafts(
    request: Request,
    status: str | None = None,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> list[dict[str, Any]]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.list_agent_authoring_drafts(
            status=status,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/drafts/{draft_id}", response_model=dict[str, Any])
async def get_draft(
    draft_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.get_agent_authoring_draft(
            draft_id,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/drafts", response_model=dict[str, Any])
async def save_draft(
    body: SaveDraftRequest,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.save_agent_authoring_draft(
            body.model_dump(mode="json"),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/drafts/{draft_id}/submit", response_model=dict[str, Any])
async def submit_draft(
    draft_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.submit_agent_authoring_draft(
            draft_id,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_authoring",
            action="draft_submitted_for_review",
            outcome="success",
            detail=f"draft_id={draft_id}",
        )
        return result
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/drafts/{draft_id}/changes-requested", response_model=dict[str, Any])
async def request_changes(
    draft_id: str,
    body: ChangesRequestedRequest,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.request_agent_authoring_changes(
            draft_id,
            body.model_dump(mode="json"),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_authoring",
            action="draft_changes_requested",
            outcome="success",
            detail=f"draft_id={draft_id}",
        )
        return result
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/drafts/{draft_id}/approve", response_model=dict[str, Any])
async def approve_draft(
    draft_id: str,
    body: ReviewActionRequest,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.approve_agent_authoring_draft(
            draft_id,
            body.model_dump(mode="json"),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_authoring",
            action="draft_approved",
            outcome="success",
            detail=f"draft_id={draft_id}",
        )
        return result
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/drafts/{draft_id}/constraint-policy", response_model=dict[str, Any])
async def patch_constraint_policy(
    draft_id: str,
    body: ConstraintPolicyPatchRequest,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.patch_agent_authoring_constraint_policy(
            draft_id,
            body.model_dump(mode="json"),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlantAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc