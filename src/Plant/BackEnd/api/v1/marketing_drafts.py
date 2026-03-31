"""Marketing draft batch endpoints.

Phase 1: Plant supports generating a persisted draft batch for review.
No external posting occurs in this module.
"""

from __future__ import annotations

import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, Request
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ChannelName, SkillExecutionInput
from core.database import get_db_session, get_read_db_session
from core.exceptions import PolicyEnforcementError
from services.draft_batches import DatabaseDraftBatchStore, DraftBatchRecord, DraftPostRecord
from services.policy_denial_audit import (
    PolicyDenialAuditRecord,
    PolicyDenialAuditStore,
    get_policy_denial_audit_store,
)
from services.marketing_credential_resolver import resolve_youtube_secret_ref

router = waooaw_router(prefix="/marketing", tags=["marketing"])

@lru_cache(maxsize=1)
def _marketing_multichannel_playbook():
    path = (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )
    return load_playbook(path)

class CreateDraftBatchRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    hired_instance_id: Optional[str] = None
    campaign_id: Optional[str] = None
    customer_id: Optional[str] = None

    theme: str
    brand_name: str
    brief_summary: Optional[str] = None
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    youtube_credential_ref: Optional[str] = None
    youtube_visibility: str = "private"
    public_release_requested: bool = False

    channels: Optional[List[ChannelName]] = None

class CreateDraftBatchResponse(DraftBatchRecord):
    pass

@router.get("/draft-batches", response_model=List[DraftBatchRecord])
async def list_draft_batches(
    agent_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[DraftBatchRecord]:
    store = DatabaseDraftBatchStore(db)
    batches = await store.load_batches()
    if agent_id:
        batches = [b for b in batches if b.agent_id == agent_id]
    if customer_id:
        batches = [b for b in batches if b.customer_id == customer_id]
    if status:
        batches = [b for b in batches if b.status == status]

    batches = batches[-max(1, int(limit)) :]
    return batches

@router.get("/draft-batches/{batch_id}", response_model=DraftBatchRecord)
async def get_draft_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> DraftBatchRecord:
    store = DatabaseDraftBatchStore(db)
    batch = await store.get_batch(batch_id)
    if batch is not None:
        return batch
    raise PolicyEnforcementError(
        "Unknown draft batch",
        reason="unknown_batch_id",
        details={"batch_id": batch_id},
    )

@router.post("/draft-batches", response_model=CreateDraftBatchResponse)
async def create_draft_batch(
    body: CreateDraftBatchRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CreateDraftBatchResponse:
    store = DatabaseDraftBatchStore(db)
    playbook = _marketing_multichannel_playbook()
    youtube_secret_ref = await resolve_youtube_secret_ref(
        db,
        hired_instance_id=body.hired_instance_id,
        supplied_ref=body.youtube_credential_ref,
    )

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme=body.theme,
            brand_name=body.brand_name,
            offer=body.offer,
            location=body.location,
            audience=body.audience,
            tone=body.tone,
            language=body.language,
            channels=body.channels,
        ),
    )

    batch_id = str(uuid4())
    posts = [
        DraftPostRecord(
            post_id=str(uuid4()),
            channel=v.channel,
            text=v.text,
            hashtags=v.hashtags,
            credential_ref=youtube_secret_ref if v.channel == ChannelName.YOUTUBE else None,
            visibility=body.youtube_visibility if v.channel == ChannelName.YOUTUBE else "private",
            public_release_requested=body.public_release_requested if v.channel == ChannelName.YOUTUBE else False,
        )
        for v in result.output.variants
    ]

    batch = DraftBatchRecord(
        batch_id=batch_id,
        agent_id=body.agent_id,
        hired_instance_id=body.hired_instance_id,
        campaign_id=body.campaign_id,
        customer_id=body.customer_id,
        theme=result.output.canonical.theme,
        brand_name=body.brand_name,
        brief_summary=body.brief_summary,
        created_at=datetime.utcnow(),
        posts=posts,
    )

    await store.save_batch(batch)
    await db.commit()
    return CreateDraftBatchResponse(**batch.model_dump())

class ExecuteDraftPostRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    purpose: Optional[str] = None

    intent_action: str = Field(default="publish", min_length=1)
    approval_id: Optional[str] = None

    correlation_id: Optional[str] = None

class ExecuteDraftPostResponse(BaseModel):
    allowed: bool
    decision_id: str
    post_id: str
    execution_status: Optional[str] = None
    provider_post_id: Optional[str] = None
    provider_post_url: Optional[str] = None

class ApproveDraftPostRequest(BaseModel):
    approval_id: Optional[str] = None

class ApproveDraftPostResponse(BaseModel):
    post_id: str
    review_status: str
    approval_id: str

@router.post("/draft-posts/{post_id}/approve", response_model=ApproveDraftPostResponse)
async def approve_draft_post(
    post_id: str,
    body: ApproveDraftPostRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ApproveDraftPostResponse:
    store = DatabaseDraftBatchStore(db)
    found = await store.find_post(post_id)
    if found is None:
        raise PolicyEnforcementError(
            "Unknown draft post",
            reason="unknown_post_id",
            details={"post_id": post_id},
        )

    approval_id = (body.approval_id or f"APR-{uuid4()}" ).strip()
    if not approval_id:
        approval_id = f"APR-{uuid4()}"

    updated = await store.update_post(post_id, review_status="approved", approval_id=approval_id)
    if not updated:
        raise PolicyEnforcementError(
            "Unable to update draft post",
            reason="update_failed",
            details={"post_id": post_id},
        )

    await db.commit()
    return ApproveDraftPostResponse(post_id=post_id, review_status="approved", approval_id=approval_id)


class RejectDraftPostResponse(BaseModel):
    post_id: str
    review_status: str


@router.post("/draft-posts/{post_id}/reject", response_model=RejectDraftPostResponse)
async def reject_draft_post(
    post_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> RejectDraftPostResponse:
    store = DatabaseDraftBatchStore(db)
    found = await store.find_post(post_id)
    if found is None:
        raise PolicyEnforcementError(
            "Unknown draft post",
            reason="unknown_post_id",
            details={"post_id": post_id},
        )

    updated = await store.update_post(
        post_id,
        review_status="rejected",
        approval_id=None,
        execution_status="not_scheduled",
        scheduled_at=None,
        last_error=None,
    )
    if not updated:
        raise PolicyEnforcementError(
            "Unable to update draft post",
            reason="update_failed",
            details={"post_id": post_id},
        )

    await db.commit()
    return RejectDraftPostResponse(post_id=post_id, review_status="rejected")

class ScheduleDraftPostRequest(BaseModel):
    scheduled_at: datetime
    approval_id: Optional[str] = None

class ScheduleDraftPostResponse(BaseModel):
    post_id: str
    execution_status: str
    scheduled_at: str

@router.post("/draft-posts/{post_id}/schedule", response_model=ScheduleDraftPostResponse)
async def schedule_draft_post(
    post_id: str,
    body: ScheduleDraftPostRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleDraftPostResponse:
    store = DatabaseDraftBatchStore(db)
    found = await store.find_post(post_id)
    if found is None:
        raise PolicyEnforcementError(
            "Unknown draft post",
            reason="unknown_post_id",
            details={"post_id": post_id},
        )

    batch, post = found
    if post.review_status != "approved":
        raise PolicyEnforcementError(
            "Draft post is not approved",
            reason="not_approved",
            details={"post_id": post_id, "review_status": post.review_status},
        )

    approval_id = (body.approval_id or post.approval_id or "").strip() or None
    if not approval_id:
        raise PolicyEnforcementError(
            "Missing approval_id for scheduling",
            reason="approval_required",
            details={"post_id": post_id},
        )

    updated = await store.update_post(
        post_id,
        execution_status="scheduled",
        scheduled_at=body.scheduled_at,
        approval_id=approval_id,
        last_error=None,
    )
    if not updated:
        raise PolicyEnforcementError(
            "Unable to schedule draft post",
            reason="update_failed",
            details={"post_id": post_id},
        )

    await db.commit()
    return ScheduleDraftPostResponse(
        post_id=post_id,
        execution_status="scheduled",
        scheduled_at=body.scheduled_at.isoformat(),
    )

@router.post("/draft-posts/{post_id}/execute", response_model=ExecuteDraftPostResponse)
async def execute_draft_post(
    post_id: str,
    body: ExecuteDraftPostRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> ExecuteDraftPostResponse:
    store = DatabaseDraftBatchStore(db)
    found = await store.find_post(post_id)
    if found is None:
        raise PolicyEnforcementError(
            "Unknown draft post",
            reason="unknown_post_id",
            details={"post_id": post_id},
        )

    batch, post = found
    correlation_id = body.correlation_id or str(uuid4())
    requested_approval_id = (body.approval_id or "").strip() or None
    stored_approval_id = (post.approval_id or "").strip() or None

    if requested_approval_id and stored_approval_id and requested_approval_id != stored_approval_id:
        details = {
            "post_id": post_id,
            "correlation_id": correlation_id,
            "message": "Invalid approval_id for execution",
        }
        policy_audit.append(
            PolicyDenialAuditRecord(
                correlation_id=correlation_id,
                decision_id="",
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                stage=str(HookStage.PRE_TOOL_USE),
                action=body.intent_action,
                reason="approval_invalid",
                path=str(request.url.path),
                details=details,
            )
        )
        raise PolicyEnforcementError(
            "Policy denied tool use",
            reason="approval_invalid",
            details=details,
        )

    effective_approval_id = requested_approval_id or stored_approval_id

    decision = default_hook_bus().emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id=correlation_id,
            agent_id=body.agent_id,
            customer_id=body.customer_id,
            purpose=body.purpose,
            action=body.intent_action,
            payload={"approval_id": effective_approval_id, "post_id": post_id},
        )
    )

    if not decision.allowed:
        details = dict(decision.details or {})
        details["decision_id"] = decision.decision_id
        details["correlation_id"] = correlation_id
        details["post_id"] = post_id

        policy_audit.append(
            PolicyDenialAuditRecord(
                correlation_id=correlation_id,
                decision_id=decision.decision_id,
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                stage=str(HookStage.PRE_TOOL_USE),
                action=body.intent_action,
                reason=decision.reason,
                path=str(request.url.path),
                details=details,
            )
        )
        raise PolicyEnforcementError(
            "Policy denied tool use",
            reason=decision.reason,
            details=details,
        )

    # For YouTube posts that are approved and have credential_ref, publish immediately.
    effective_credential_ref = await resolve_youtube_secret_ref(
        db,
        hired_instance_id=batch.hired_instance_id,
        supplied_ref=post.credential_ref,
    )

    if (
        post.channel.value == "youtube"
        and post.review_status == "approved"
        and effective_credential_ref
    ):
        try:
            from integrations.social.youtube_client import YouTubeClient

            client = YouTubeClient(customer_id=batch.customer_id)
            result = await client.post_text(
                credential_ref=effective_credential_ref,
                text=post.text,
            )
            provider_post_id = result.post_id
            provider_post_url = result.post_url

            await store.update_post(
                post_id,
                credential_ref=effective_credential_ref,
                execution_status="posted",
                provider_post_id=provider_post_id,
                provider_post_url=provider_post_url,
                last_error=None,
            )
            await db.commit()

            return ExecuteDraftPostResponse(
                allowed=True,
                decision_id=decision.decision_id or "",
                post_id=post_id,
                execution_status="posted",
                provider_post_id=provider_post_id,
                provider_post_url=provider_post_url,
            )
        except Exception as exc:
            await store.update_post(
                post_id,
                execution_status="failed",
                last_error=str(exc),
            )
            await db.commit()
            raise PolicyEnforcementError(
                "YouTube publish failed",
                reason="publish_failed",
                details={"post_id": post_id, "error": str(exc)},
            )

    return ExecuteDraftPostResponse(
        allowed=True,
        decision_id=decision.decision_id or "",
        post_id=post_id,
    )
