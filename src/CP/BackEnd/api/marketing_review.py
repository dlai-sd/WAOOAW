"""Customer-scoped marketing draft review routes (CP).

These endpoints wrap Plant's marketing draft-batch review APIs and inject the
correct customer_id derived from the authenticated CP user.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.cp_approvals import FileCPApprovalStore, get_cp_approval_store
from services.plant_gateway_client import PlantGatewayClient


router = APIRouter(prefix="/cp/marketing", tags=["cp-marketing"])


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


def get_plant_gateway_client() -> PlantGatewayClient:
    base_url = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        headers["X-Correlation-ID"] = correlation
    debug = request.headers.get("x-debug-trace")
    if debug:
        headers["X-Debug-Trace"] = debug
    return headers


def _find_post_in_batches(batches: List[Dict[str, Any]], *, post_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    for batch in batches:
        posts = batch.get("posts") or []
        for post in posts:
            if str(post.get("post_id")) == post_id:
                return batch, post
    return None


def _apply_cp_rejection_overlay(
    *,
    batches: List[Dict[str, Any]],
    customer_id: str,
    approvals: FileCPApprovalStore,
) -> List[Dict[str, Any]]:
    records = approvals.list(customer_id=customer_id, limit=500)
    last_decision_by_post_id: Dict[str, str] = {}
    for rec in records:
        if rec.subject_type != "marketing_draft_post":
            continue
        last_decision_by_post_id[str(rec.subject_id)] = str(rec.decision)

    rejected_ids = {pid for pid, decision in last_decision_by_post_id.items() if decision == "rejected"}
    if not rejected_ids:
        return batches

    filtered_batches: List[Dict[str, Any]] = []
    for batch in batches:
        posts = batch.get("posts") or []
        kept = [p for p in posts if str(p.get("post_id")) not in rejected_ids]
        if not kept:
            continue
        new_batch = dict(batch)
        new_batch["posts"] = kept
        filtered_batches.append(new_batch)

    return filtered_batches


@router.get("/draft-batches", response_model=List[Dict[str, Any]])
async def list_draft_batches(
    request: Request,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
    approvals: FileCPApprovalStore = Depends(get_cp_approval_store),
) -> List[Dict[str, Any]]:
    params: Dict[str, str] = {"customer_id": _customer_id_from_user(current_user), "limit": str(limit)}
    if agent_id:
        params["agent_id"] = agent_id
    if status:
        params["status"] = status

    resp = await plant.request_json(
        method="GET",
        path="api/v1/marketing/draft-batches",
        headers=_forward_headers(request),
        params=params,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    if isinstance(resp.json, list):
        return _apply_cp_rejection_overlay(batches=resp.json, customer_id=params["customer_id"], approvals=approvals)
    return []


class ApproveDraftPostRequest(BaseModel):
    post_id: str = Field(..., min_length=1)


class ApproveDraftPostResponse(BaseModel):
    post_id: str
    review_status: str
    approval_id: str


@router.post("/draft-posts/approve", response_model=ApproveDraftPostResponse)
async def approve_draft_post(
    body: ApproveDraftPostRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
    approvals: FileCPApprovalStore = Depends(get_cp_approval_store),
) -> ApproveDraftPostResponse:
    customer_id = _customer_id_from_user(current_user)

    approval = approvals.append(
        customer_id=customer_id,
        subject_type="marketing_draft_post",
        subject_id=body.post_id,
        action="publish",
        decision="approved",
    )

    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/marketing/draft-posts/{body.post_id}/approve",
        headers=_forward_headers(request),
        json_body={"approval_id": approval.approval_id},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    payload = resp.json if isinstance(resp.json, dict) else {}
    return ApproveDraftPostResponse(
        post_id=str(payload.get("post_id") or body.post_id),
        review_status=str(payload.get("review_status") or "approved"),
        approval_id=str(payload.get("approval_id") or approval.approval_id),
    )


class RejectDraftPostRequest(BaseModel):
    post_id: str = Field(..., min_length=1)
    reason: Optional[str] = None


class RejectDraftPostResponse(BaseModel):
    post_id: str
    decision: str


@router.post("/draft-posts/reject", response_model=RejectDraftPostResponse)
async def reject_draft_post(
    body: RejectDraftPostRequest,
    current_user: User = Depends(get_current_user),
    approvals: FileCPApprovalStore = Depends(get_cp_approval_store),
) -> RejectDraftPostResponse:
    # Plant doesn't currently expose a reject endpoint for draft posts.
    # CP records the rejection and prevents scheduling/execution in CP UX.
    approvals.append(
        customer_id=_customer_id_from_user(current_user),
        subject_type="marketing_draft_post",
        subject_id=body.post_id,
        action="publish",
        decision="rejected",
        reason=body.reason,
    )
    return RejectDraftPostResponse(post_id=body.post_id, decision="rejected")


class ScheduleDraftPostRequest(BaseModel):
    post_id: str = Field(..., min_length=1)
    scheduled_at: datetime
    approval_id: Optional[str] = None


class ScheduleDraftPostResponse(BaseModel):
    post_id: str
    execution_status: str
    scheduled_at: str


@router.post("/draft-posts/schedule", response_model=ScheduleDraftPostResponse)
async def schedule_draft_post(
    body: ScheduleDraftPostRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> ScheduleDraftPostResponse:
    customer_id = _customer_id_from_user(current_user)

    batches_resp = await plant.request_json(
        method="GET",
        path="api/v1/marketing/draft-batches",
        headers=_forward_headers(request),
        params={"customer_id": customer_id, "limit": "200"},
    )
    if batches_resp.status_code != 200:
        raise HTTPException(status_code=batches_resp.status_code, detail=batches_resp.json)

    batches = batches_resp.json if isinstance(batches_resp.json, list) else []
    found = _find_post_in_batches(batches, post_id=body.post_id)
    if found is None:
        raise HTTPException(status_code=404, detail={"error": "unknown_post_id", "post_id": body.post_id})

    _batch, post = found
    if str(post.get("review_status")) != "approved":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "not_approved",
                "post_id": body.post_id,
                "review_status": post.get("review_status"),
            },
        )

    schedule_body: Dict[str, Any] = {
        "scheduled_at": body.scheduled_at.isoformat(),
    }
    if body.approval_id:
        schedule_body["approval_id"] = body.approval_id

    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/marketing/draft-posts/{body.post_id}/schedule",
        headers=_forward_headers(request),
        json_body=schedule_body,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    payload = resp.json if isinstance(resp.json, dict) else {}
    return ScheduleDraftPostResponse(
        post_id=str(payload.get("post_id") or body.post_id),
        execution_status=str(payload.get("execution_status") or "scheduled"),
        scheduled_at=str(payload.get("scheduled_at") or body.scheduled_at.isoformat()),
    )
