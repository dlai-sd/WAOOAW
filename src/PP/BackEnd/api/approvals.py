"""Approval endpoints (PP).

Phase 1: admin-only routes to mint approvals that can be used as `approval_id`
when invoking approval-gated actions in Plant (e.g. trading).

MVP review-queue support adds a thin enrichment route that combines PP approval
records with Plant hired-agent and marketing draft context so PP operators can
render actionable review cards without reconstructive fetches in the UI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from services.approvals import ApprovalRecord, FileApprovalStore, get_approval_store


from core.routing import waooaw_router  # PP-N3b
from core.observability import get_pp_tracer  # E7: OTel spans
from core.metrics import pp_approval_counter  # E8: Prometheus metrics
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/approvals", tags=["approvals"])

_tracer = get_pp_tracer()


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
    request: Request,
    claims: Dict[str, Any] = Depends(require_admin),
    store: FileApprovalStore = Depends(get_approval_store),
    audit: AuditLogger = Depends(get_audit_logger),  # PP-N4
) -> ApprovalResponse:
    with _tracer.start_as_current_span("pp.approvals.mint") as span:
        if hasattr(span, "set_attribute"):
            span.set_attribute("pp.approval.action", body.action)
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
        if hasattr(span, "set_attribute"):
            span.set_attribute("pp.approval.id", saved.approval_id)
        pp_approval_counter.labels(outcome="success").inc()  # E8: Prometheus metric
        # PP-N4: fire-and-forget audit event — approval minted
        await audit.log(
            "pp_approvals",
            "approval_minted",
            "success",
            detail=f"Approval {saved.approval_id} minted: customer={body.customer_id} agent={body.agent_id} action={body.action}",
            metadata={"approval_id": saved.approval_id, "action": body.action},
        )
        return _to_response(saved)


class ApprovalListResponse(BaseModel):
    count: int
    approvals: List[Dict[str, Any]]


class DeliverablePreviewResponse(BaseModel):
    batch_id: Optional[str] = None
    post_id: Optional[str] = None
    brand_name: Optional[str] = None
    theme: Optional[str] = None
    channel: Optional[str] = None
    text_preview: Optional[str] = None


class PublishDiagnosticsResponse(BaseModel):
    publish_block: str
    publish_reason: str
    credential_state: str
    approval_lineage: str
    youtube_visibility: Optional[str] = None
    public_release_requested: bool = False
    last_error: Optional[str] = None


class ReviewQueueApprovalResponse(BaseModel):
    approval_id: str
    customer_id: str
    customer_label: str
    agent_id: str
    agent_label: str
    action: str
    requested_by: str
    correlation_id: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None
    hired_instance_id: Optional[str] = None
    review_state: str
    deliverable_preview: DeliverablePreviewResponse = Field(default_factory=DeliverablePreviewResponse)
    publish_diagnostics: PublishDiagnosticsResponse


class ReviewQueueApprovalListResponse(BaseModel):
    count: int
    approvals: List[ReviewQueueApprovalResponse]


def _truncate_preview(text: Any, limit: int = 140) -> Optional[str]:
    value = str(text or '').strip()
    if not value:
        return None
    if len(value) <= limit:
        return value
    return f"{value[: limit - 1].rstrip()}…"


def _normalize_publish_reason(reason: Optional[str]) -> str:
    value = str(reason or "").strip().lower()
    if value == "approval_required_for_youtube_publish":
        return "The scheduler refused to publish because the exact deliverable has no approval id."
    if value == "credential_ref_required_for_youtube_publish":
        return "The draft is approved, but the YouTube credential reference is still missing."
    if value == "public_release_requires_explicit_customer_action":
        return "Upload can stay non-public, but public release still needs explicit customer action."
    if value:
        return f"The latest scheduler or publish attempt failed with: {value}."
    return "No publish blocker has been recorded yet."


def _derive_publish_diagnostics(draft_batch: Optional[Dict[str, Any]]) -> PublishDiagnosticsResponse:
    posts = list(draft_batch.get("posts") or []) if draft_batch else []
    first_post = posts[0] if posts else {}

    review_status = str(first_post.get("review_status") or draft_batch.get("status") or "pending_review").strip().lower()
    execution_status = str(first_post.get("execution_status") or "not_scheduled").strip().lower()
    channel = str(first_post.get("channel") or draft_batch.get("channel") or "").strip().lower()
    approval_id = str(first_post.get("approval_id") or "").strip() or None
    credential_ref = str(
        first_post.get("credential_ref")
        or draft_batch.get("youtube_credential_ref")
        or draft_batch.get("credential_ref")
        or ""
    ).strip() or None
    visibility = str(first_post.get("visibility") or draft_batch.get("youtube_visibility") or "private").strip().lower() or "private"
    public_release_requested = bool(
        first_post.get("public_release_requested")
        or draft_batch.get("public_release_requested")
    )
    last_error = str(first_post.get("last_error") or draft_batch.get("last_error") or "").strip() or None
    post_id = str(first_post.get("post_id") or "").strip() or None

    if approval_id and post_id:
        approval_lineage = f"Approval {approval_id} is currently attached to post {post_id}."
    elif approval_id:
        approval_lineage = f"Approval {approval_id} exists, but the exact post id was not returned."
    else:
        approval_lineage = "No approval id is attached to the exact deliverable yet."

    if review_status == "rejected":
        return PublishDiagnosticsResponse(
            publish_block="customer_rejection",
            publish_reason="The customer rejected this draft, so a revised deliverable must be approved before anything can publish.",
            credential_state="not_applicable_until_reapproved",
            approval_lineage=approval_lineage,
            youtube_visibility=visibility if channel == "youtube" else None,
            public_release_requested=public_release_requested,
            last_error=last_error,
        )

    if not approval_id:
        return PublishDiagnosticsResponse(
            publish_block="approval_missing",
            publish_reason="The draft is still blocked on exact customer approval before publish can proceed.",
            credential_state="pending_after_approval",
            approval_lineage=approval_lineage,
            youtube_visibility=visibility if channel == "youtube" else None,
            public_release_requested=public_release_requested,
            last_error=last_error,
        )

    if channel == "youtube" and not credential_ref:
        return PublishDiagnosticsResponse(
            publish_block="credential_missing",
            publish_reason=_normalize_publish_reason(last_error or "credential_ref_required_for_youtube_publish"),
            credential_state="missing_youtube_credential_ref",
            approval_lineage=approval_lineage,
            youtube_visibility=visibility,
            public_release_requested=public_release_requested,
            last_error=last_error,
        )

    if last_error == "public_release_requires_explicit_customer_action" or (
        execution_status == "executed" and channel == "youtube" and visibility != "public"
    ):
        return PublishDiagnosticsResponse(
            publish_block="awaiting_public_release",
            publish_reason=_normalize_publish_reason(last_error or "public_release_requires_explicit_customer_action"),
            credential_state="credential_present",
            approval_lineage=approval_lineage,
            youtube_visibility=visibility if channel == "youtube" else None,
            public_release_requested=public_release_requested,
            last_error=last_error,
        )

    if last_error:
        block = "scheduler_denial" if "policy" in last_error.lower() or "denied" in last_error.lower() else "publish_failed"
        return PublishDiagnosticsResponse(
            publish_block=block,
            publish_reason=_normalize_publish_reason(last_error),
            credential_state="credential_present" if credential_ref else "unknown",
            approval_lineage=approval_lineage,
            youtube_visibility=visibility if channel == "youtube" else None,
            public_release_requested=public_release_requested,
            last_error=last_error,
        )

    return PublishDiagnosticsResponse(
        publish_block="ready_or_inflight",
        publish_reason="Approval lineage and credentials are present. PP should inspect scheduler and hook diagnostics for the next runtime step.",
        credential_state="credential_present" if credential_ref else "unknown",
        approval_lineage=approval_lineage,
        youtube_visibility=visibility if channel == "youtube" else None,
        public_release_requested=public_release_requested,
        last_error=last_error,
    )


async def _fetch_hired_agents_by_customer(
    *,
    customer_id: str,
    auth_header: Optional[str],
    client: PlantAPIClient,
) -> List[Dict[str, Any]]:
    response = await client._request(
        method="GET",
        path=f"/api/v1/hired-agents/by-customer/{customer_id}",
        headers={"Authorization": auth_header} if auth_header else None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    body = response.json()
    if isinstance(body, dict):
        return list(body.get("instances") or [])
    if isinstance(body, list):
        return body
    return []


async def _fetch_customer_summary(
    *,
    customer_id: str,
    auth_header: Optional[str],
    client: PlantAPIClient,
) -> Dict[str, Any]:
    response = await client._request(
        method="GET",
        path=f"/api/v1/customers/{customer_id}",
        headers={"Authorization": auth_header} if auth_header else None,
    )
    if response.status_code != 200:
        return {}

    body = response.json()
    return body if isinstance(body, dict) else {}


async def _fetch_draft_batches(
    *,
    customer_id: str,
    agent_id: Optional[str],
    auth_header: Optional[str],
    client: PlantAPIClient,
    limit: int,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "customer_id": customer_id,
        "status": "pending_review",
        "limit": limit,
    }
    if agent_id:
        params["agent_id"] = agent_id

    response = await client._request(
        method="GET",
        path="/api/v1/marketing/draft-batches",
        params=params,
        headers={"Authorization": auth_header} if auth_header else None,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    body = response.json()
    return body if isinstance(body, list) else []


def _match_hired_instance(agent_id: str, hired_agents: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for instance in hired_agents:
        if str(instance.get("agent_id") or "") == agent_id:
            return instance
    return None


def _match_draft_batch(agent_id: str, draft_batches: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for batch in draft_batches:
        if str(batch.get("agent_id") or "") == agent_id:
            return batch
    return None


def _customer_label(customer_summary: Optional[Dict[str, Any]], fallback_customer_id: str) -> str:
    if customer_summary:
        email = str(customer_summary.get("email") or "").strip()
        if email:
            return email
    return fallback_customer_id


def _agent_label(hired_instance: Optional[Dict[str, Any]], fallback_agent_id: str) -> str:
    if hired_instance:
        nickname = str(hired_instance.get("nickname") or "").strip()
        if nickname:
            return nickname
    return fallback_agent_id


def _to_review_queue_response(
    approval: ApprovalRecord,
    *,
    customer_summary: Optional[Dict[str, Any]],
    hired_instance: Optional[Dict[str, Any]],
    draft_batch: Optional[Dict[str, Any]],
) -> ReviewQueueApprovalResponse:
    posts = list(draft_batch.get("posts") or []) if draft_batch else []
    first_post = posts[0] if posts else {}
    review_state = str(first_post.get("review_status") or draft_batch.get("status") or "context_unavailable")

    return ReviewQueueApprovalResponse(
        approval_id=approval.approval_id,
        customer_id=approval.customer_id,
        customer_label=_customer_label(customer_summary, approval.customer_id),
        agent_id=approval.agent_id,
        agent_label=_agent_label(hired_instance, approval.agent_id),
        action=approval.action,
        requested_by=approval.requested_by,
        correlation_id=approval.correlation_id,
        purpose=approval.purpose,
        notes=approval.notes,
        created_at=approval.created_at.isoformat(),
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
        hired_instance_id=(hired_instance or {}).get("hired_instance_id"),
        review_state=review_state,
        deliverable_preview=DeliverablePreviewResponse(
            batch_id=(draft_batch or {}).get("batch_id"),
            post_id=first_post.get("post_id"),
            brand_name=(draft_batch or {}).get("brand_name"),
            theme=(draft_batch or {}).get("theme"),
            channel=first_post.get("channel"),
            text_preview=_truncate_preview(first_post.get("text")),
        ),
        publish_diagnostics=_derive_publish_diagnostics(draft_batch),
    )


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    action: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = 100,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileApprovalStore = Depends(get_approval_store),
) -> ApprovalListResponse:
    rows = store.list(customer_id=customer_id, agent_id=agent_id, action=action, correlation_id=correlation_id, limit=limit)
    return ApprovalListResponse(count=len(rows), approvals=[_to_response(r).model_dump(mode="json") for r in rows])


@router.get("/review-queue", response_model=ReviewQueueApprovalListResponse)
async def list_review_queue_approvals(
    request: Request,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    action: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = 20,
    _claims: Dict[str, Any] = Depends(require_admin),
    auth_header: Optional[str] = Depends(get_authorization_header),
    store: FileApprovalStore = Depends(get_approval_store),
    client: PlantAPIClient = Depends(get_plant_client),
) -> ReviewQueueApprovalListResponse:
    rows = store.list(
        customer_id=customer_id,
        agent_id=agent_id,
        action=action,
        correlation_id=correlation_id,
        limit=limit,
    )

    if not rows:
        return ReviewQueueApprovalListResponse(count=0, approvals=[])

    hired_agents_by_customer: Dict[str, List[Dict[str, Any]]] = {}
    customers_by_id: Dict[str, Dict[str, Any]] = {}
    draft_batches_by_context: Dict[tuple[str, str], List[Dict[str, Any]]] = {}

    try:
        for row in rows:
            if row.customer_id not in customers_by_id:
                customers_by_id[row.customer_id] = await _fetch_customer_summary(
                    customer_id=row.customer_id,
                    auth_header=auth_header,
                    client=client,
                )

            if row.customer_id not in hired_agents_by_customer:
                hired_agents_by_customer[row.customer_id] = await _fetch_hired_agents_by_customer(
                    customer_id=row.customer_id,
                    auth_header=auth_header,
                    client=client,
                )

            context_key = (row.customer_id, row.agent_id)
            if context_key not in draft_batches_by_context:
                draft_batches_by_context[context_key] = await _fetch_draft_batches(
                    customer_id=row.customer_id,
                    agent_id=row.agent_id,
                    auth_header=auth_header,
                    client=client,
                    limit=limit,
                )
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    approvals = [
        _to_review_queue_response(
            row,
            customer_summary=customers_by_id.get(row.customer_id),
            hired_instance=_match_hired_instance(row.agent_id, hired_agents_by_customer.get(row.customer_id, [])),
            draft_batch=_match_draft_batch(row.agent_id, draft_batches_by_context.get((row.customer_id, row.agent_id), [])),
        )
        for row in rows
    ]
    return ReviewQueueApprovalListResponse(count=len(approvals), approvals=approvals)


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
