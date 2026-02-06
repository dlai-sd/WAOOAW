"""Approval endpoints (PP).

Phase 1: admin-only routes to mint approvals that can be used as `approval_id`
when invoking approval-gated actions in Plant (e.g. trading).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import require_admin
from services.approvals import ApprovalRecord, FileApprovalStore, get_approval_store


router = APIRouter(prefix="/approvals", tags=["approvals"])


class MintApprovalRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)

    correlation_id: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None

    expires_in_seconds: Optional[int] = None
    approval_id: Optional[str] = None


class ApprovalResponse(BaseModel):
    approval_id: str
    customer_id: str
    agent_id: str
    action: str
    requested_by: str
    correlation_id: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None


def _to_response(model: ApprovalRecord) -> ApprovalResponse:
    return ApprovalResponse(
        approval_id=model.approval_id,
        customer_id=model.customer_id,
        agent_id=model.agent_id,
        action=model.action,
        requested_by=model.requested_by,
        correlation_id=model.correlation_id,
        purpose=model.purpose,
        notes=model.notes,
        created_at=model.created_at.isoformat(),
        expires_at=model.expires_at.isoformat() if model.expires_at else None,
    )


@router.post("", response_model=ApprovalResponse)
async def mint_approval(
    body: MintApprovalRequest,
    claims: Dict[str, Any] = Depends(require_admin),
    store: FileApprovalStore = Depends(get_approval_store),
) -> ApprovalResponse:
    requested_by = str(claims.get("sub") or "admin").strip() or "admin"
    saved = store.create(
        customer_id=body.customer_id,
        agent_id=body.agent_id,
        action=body.action,
        requested_by=requested_by,
        correlation_id=body.correlation_id,
        purpose=body.purpose,
        notes=body.notes,
        expires_in_seconds=body.expires_in_seconds,
        approval_id=body.approval_id,
    )
    return _to_response(saved)


class ApprovalListResponse(BaseModel):
    count: int
    approvals: List[Dict[str, Any]]


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileApprovalStore = Depends(get_approval_store),
) -> ApprovalListResponse:
    rows = store.list(customer_id=customer_id, agent_id=agent_id, action=action, limit=limit)
    return ApprovalListResponse(count=len(rows), approvals=[_to_response(r).model_dump(mode="json") for r in rows])


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileApprovalStore = Depends(get_approval_store),
) -> ApprovalResponse:
    row = store.get(approval_id=approval_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return _to_response(row)
