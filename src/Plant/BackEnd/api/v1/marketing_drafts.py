"""Marketing draft batch endpoints.

Phase 1: Plant supports generating a persisted draft batch for review.
No external posting occurs in this module.
"""

from __future__ import annotations

import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, Request
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.skills.artifact_routing import route_artifact_requests
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ArtifactRequest, ArtifactType, ChannelName, GeneratedArtifactReference, SkillExecutionInput
from core.database import get_db_session, get_read_db_session
from core.exceptions import PolicyEnforcementError
from services.draft_batches import DatabaseDraftBatchStore, DraftBatchRecord, DraftPostRecord, materialize_batch_record
from services.media_artifact_store import get_media_artifact_store
from services.policy_denial_audit import (
    PolicyDenialAuditRecord,
    PolicyDenialAuditStore,
    get_policy_denial_audit_store,
)
from services.marketing_credential_resolver import resolve_youtube_secret_ref
from services.social_credential_resolver import DatabaseCredentialResolver
from worker.tasks.media_generation_tasks import enqueue_media_generation_job

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

    # Workflow stage: 'theme' = content-plan/table batch, 'content' = actual post batch, 'direct' = single-step
    batch_type: str = "direct"
    # Links a content batch back to the theme batch that it was derived from
    parent_batch_id: Optional[str] = None

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
    requested_artifacts: Optional[List[ArtifactRequest]] = None

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
    return [materialize_batch_record(batch) for batch in batches]

@router.get("/draft-batches/{batch_id}", response_model=DraftBatchRecord)
async def get_draft_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> DraftBatchRecord:
    store = DatabaseDraftBatchStore(db)
    batch = await store.get_batch(batch_id)
    if batch is not None:
        return materialize_batch_record(batch)
    raise PolicyEnforcementError(
        "Unknown draft batch",
        reason="unknown_batch_id",
        details={"batch_id": batch_id},
    )

@router.post("/draft-batches", response_model=CreateDraftBatchResponse)
async def create_draft_batch(
    body: CreateDraftBatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> CreateDraftBatchResponse:
    store = DatabaseDraftBatchStore(db)
    playbook = _marketing_multichannel_playbook()
    media_store = get_media_artifact_store()
    youtube_secret_ref = await resolve_youtube_secret_ref(
        db,
        hired_instance_id=body.hired_instance_id,
        supplied_ref=body.youtube_credential_ref,
    )
    correlation_id = request.headers.get("x-correlation-id") or str(uuid4())

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
            requested_artifacts=body.requested_artifacts,
        ),
    )

    batch_id = str(uuid4())
    posts: List[DraftPostRecord] = []
    for variant in result.output.variants:
        post_id = str(uuid4())
        prepared = await _prepare_post_artifacts(
            batch_id=batch_id,
            post_id=post_id,
            channel=variant.channel,
            theme=body.theme,
            brand_name=body.brand_name,
            text=variant.text,
            requested_artifacts=list(result.output.canonical.requested_artifacts or []),
            pre_generated_artifacts=[
                GeneratedArtifactReference.model_validate(artifact)
                for artifact in (variant.generated_artifacts or [])
            ],
            media_store=media_store,
            correlation_id=correlation_id,
        )
        posts.append(
            DraftPostRecord(
                post_id=post_id,
                channel=variant.channel,
                text=variant.text,
                hashtags=variant.hashtags,
                artifact_type=prepared["artifact_type"],
                artifact_uri=prepared["artifact_uri"],
                artifact_preview_uri=prepared["artifact_preview_uri"],
                artifact_mime_type=prepared["artifact_mime_type"],
                artifact_metadata=prepared["artifact_metadata"],
                artifact_generation_status=prepared["artifact_generation_status"],
                artifact_job_id=prepared["artifact_job_id"],
                generated_artifacts=prepared["generated_artifacts"],
                credential_ref=youtube_secret_ref if variant.channel == ChannelName.YOUTUBE else None,
                visibility=body.youtube_visibility if variant.channel == ChannelName.YOUTUBE else "private",
                public_release_requested=body.public_release_requested if variant.channel == ChannelName.YOUTUBE else False,
            )
        )

    batch = materialize_batch_record(DraftBatchRecord(
        batch_id=batch_id,
        batch_type=body.batch_type,
        parent_batch_id=body.parent_batch_id,
        agent_id=body.agent_id,
        hired_instance_id=body.hired_instance_id,
        campaign_id=body.campaign_id,
        customer_id=body.customer_id,
        theme=result.output.canonical.theme,
        brand_name=body.brand_name,
        brief_summary=body.brief_summary,
        created_at=datetime.utcnow(),
        posts=posts,
    ))

    await store.save_batch(batch)
    await db.commit()
    return CreateDraftBatchResponse(**batch.model_dump())


class CreateContentBatchFromThemeRequest(BaseModel):
    """Request to create a content batch from an approved theme batch.

    The caller specifies what content artifacts to generate. The new batch inherits
    the hired_instance_id, campaign_id, customer_id, brand_name, and approved theme
    from the parent theme batch.
    """
    youtube_credential_ref: Optional[str] = None
    youtube_visibility: str = "private"
    public_release_requested: bool = False
    requested_artifacts: Optional[List[ArtifactRequest]] = None


@router.post("/draft-batches/{batch_id}/create-content-batch", response_model=CreateDraftBatchResponse)
async def create_content_batch_from_theme(
    batch_id: str,
    body: CreateContentBatchFromThemeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> CreateDraftBatchResponse:
    """Create a content batch from an approved theme batch.

    All posts in the theme batch must be approved. The new content batch is linked
    to the theme batch via parent_batch_id and is tagged batch_type='content'.
    """
    from core.exceptions import PolicyEnforcementError

    store = DatabaseDraftBatchStore(db)
    theme_batch = await store.get_batch(batch_id)
    if theme_batch is None:
        raise PolicyEnforcementError(
            "Unknown theme batch",
            reason="unknown_batch_id",
            details={"batch_id": batch_id},
        )

    if theme_batch.batch_type not in ("theme", "direct"):
        raise PolicyEnforcementError(
            "Only a theme batch can spawn a content batch",
            reason="invalid_batch_type",
            details={"batch_id": batch_id, "batch_type": theme_batch.batch_type},
        )

    unapproved = [p for p in theme_batch.posts if p.review_status != "approved"]
    if unapproved:
        raise PolicyEnforcementError(
            "All theme posts must be approved before creating a content batch",
            reason="theme_not_fully_approved",
            details={"unapproved_post_ids": [p.post_id for p in unapproved]},
        )

    # Use the theme text from approved posts as the content brief
    approved_theme_text = " | ".join(
        p.text[:200] for p in theme_batch.posts if p.review_status == "approved"
    )
    content_theme = approved_theme_text or theme_batch.theme

    youtube_secret_ref = await resolve_youtube_secret_ref(
        db,
        hired_instance_id=theme_batch.hired_instance_id,
        supplied_ref=body.youtube_credential_ref,
    )
    correlation_id = request.headers.get("x-correlation-id") or str(uuid4())

    playbook = _marketing_multichannel_playbook()
    media_store = get_media_artifact_store()
    channels: List[ChannelName] = list({p.channel for p in theme_batch.posts})

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme=content_theme,
            brand_name=theme_batch.brand_name,
            channels=channels,
            requested_artifacts=body.requested_artifacts,
        ),
    )

    content_batch_id = str(uuid4())
    posts: List[DraftPostRecord] = []
    for variant in result.output.variants:
        post_id = str(uuid4())
        prepared = await _prepare_post_artifacts(
            batch_id=content_batch_id,
            post_id=post_id,
            channel=variant.channel,
            theme=content_theme,
            brand_name=theme_batch.brand_name,
            text=variant.text,
            requested_artifacts=list(result.output.canonical.requested_artifacts or []),
            pre_generated_artifacts=[
                GeneratedArtifactReference.model_validate(artifact)
                for artifact in (variant.generated_artifacts or [])
            ],
            media_store=media_store,
            correlation_id=correlation_id,
        )
        posts.append(
            DraftPostRecord(
                post_id=post_id,
                channel=variant.channel,
                text=variant.text,
                hashtags=variant.hashtags,
                artifact_type=prepared["artifact_type"],
                artifact_uri=prepared["artifact_uri"],
                artifact_preview_uri=prepared["artifact_preview_uri"],
                artifact_mime_type=prepared["artifact_mime_type"],
                artifact_metadata=prepared["artifact_metadata"],
                artifact_generation_status=prepared["artifact_generation_status"],
                artifact_job_id=prepared["artifact_job_id"],
                generated_artifacts=prepared["generated_artifacts"],
                credential_ref=youtube_secret_ref if variant.channel == ChannelName.YOUTUBE else None,
                visibility=body.youtube_visibility if variant.channel == ChannelName.YOUTUBE else "private",
                public_release_requested=body.public_release_requested if variant.channel == ChannelName.YOUTUBE else False,
            )
        )

    content_batch = materialize_batch_record(DraftBatchRecord(
        batch_id=content_batch_id,
        batch_type="content",
        parent_batch_id=batch_id,
        agent_id=theme_batch.agent_id,
        hired_instance_id=theme_batch.hired_instance_id,
        campaign_id=theme_batch.campaign_id,
        customer_id=theme_batch.customer_id,
        theme=content_theme,
        brand_name=theme_batch.brand_name,
        brief_summary=f"Content batch derived from approved theme batch {batch_id}",
        created_at=datetime.utcnow(),
        posts=posts,
    ))

    await store.save_batch(content_batch)
    await db.commit()
    return CreateDraftBatchResponse(**content_batch.model_dump())


def _table_preview(theme: str, brand_name: str, channel: ChannelName, prompt: str) -> Dict[str, Any]:
    rows = [
        {
            "content_pillar": "Hook",
            "customer_angle": brand_name,
            "channel_use": channel.value,
            "prompt_hint": prompt,
        },
        {
            "content_pillar": "Proof",
            "customer_angle": theme,
            "channel_use": "CTA",
            "prompt_hint": "Show measurable value before publish",
        },
        {
            "content_pillar": "Offer",
            "customer_angle": f"{brand_name} next step",
            "channel_use": "Review",
            "prompt_hint": "Customer approves before publish",
        },
    ]
    return {
        "columns": ["content_pillar", "customer_angle", "channel_use", "prompt_hint"],
        "rows": rows,
    }


def _table_preview_csv(preview: Dict[str, Any]) -> bytes:
    columns = list(preview.get("columns") or [])
    rows = list(preview.get("rows") or [])
    lines = [",".join(columns)]
    for row in rows:
        values = [str(row.get(column, "")).replace(",", " ") for column in columns]
        lines.append(",".join(values))
    return "\n".join(lines).encode("utf-8")


async def _prepare_post_artifacts(
    *,
    batch_id: str,
    post_id: str,
    channel: ChannelName,
    theme: str,
    brand_name: str,
    text: str,
    requested_artifacts: List[ArtifactRequest],
    pre_generated_artifacts: List[GeneratedArtifactReference],
    media_store,
    correlation_id: str,
) -> Dict[str, Any]:
    generated_artifacts = list(pre_generated_artifacts)
    artifact_metadata: Dict[str, Any] = {}
    artifact_type = "text"
    artifact_uri = None
    artifact_preview_uri = None
    artifact_mime_type = None
    artifact_generation_status = "not_requested"
    artifact_job_id = None

    if generated_artifacts:
        primary_generated_artifact = generated_artifacts[0]
        artifact_type = primary_generated_artifact.artifact_type.value
        artifact_uri = primary_generated_artifact.uri
        artifact_preview_uri = primary_generated_artifact.preview_uri
        artifact_mime_type = primary_generated_artifact.mime_type
        artifact_metadata.update(primary_generated_artifact.metadata)

    accepted_requests, rejected_requests = route_artifact_requests(channel, requested_artifacts)
    if rejected_requests:
        artifact_metadata["routing_errors"] = [
            {"artifact_type": item.artifact_type.value, "reason": item.reason}
            for item in rejected_requests
        ]

    table_requests = [req for req in accepted_requests if req.artifact_type == ArtifactType.TABLE]
    queued_requests = [req for req in accepted_requests if req.artifact_type != ArtifactType.TABLE]

    if table_requests:
        table_request = table_requests[0]
        preview = _table_preview(theme, brand_name, channel, table_request.prompt)
        stored = await media_store.store_artifact(
            batch_id=batch_id,
            post_id=post_id,
            artifact_type=ArtifactType.TABLE,
            filename=f"{channel.value}-table.csv",
            content=_table_preview_csv(preview),
            mime_type="text/csv",
            metadata={
                "generation_status": "ready",
                "table_preview": preview,
                "source_text": text,
            },
        )
        table_artifact = stored.as_generated_reference()
        generated_artifacts.append(table_artifact)
        artifact_type = ArtifactType.TABLE.value
        artifact_uri = table_artifact.uri
        artifact_preview_uri = table_artifact.preview_uri
        artifact_mime_type = table_artifact.mime_type
        artifact_metadata.update(table_artifact.metadata)
        artifact_generation_status = "ready"

    if queued_requests:
        first_binary_request = queued_requests[0]
        artifact_type = first_binary_request.artifact_type.value
        artifact_generation_status = "queued"
        artifact_metadata["queued_artifact_types"] = [request.artifact_type.value for request in queued_requests]
        artifact_metadata["generation_status"] = "queued"
        artifact_job_id, dispatch_mode = enqueue_media_generation_job(
            payload={
                "correlation_id": correlation_id,
                "batch_id": batch_id,
                "post_id": post_id,
                "channel": channel.value,
                "theme": theme,
                "brand_name": brand_name,
                "text": text,
                "requested_artifacts": [request.model_dump(mode="json") for request in queued_requests],
            }
        )
        artifact_metadata["dispatch_mode"] = dispatch_mode

    if accepted_requests or rejected_requests:
        artifact_metadata["requested_artifacts"] = [request.model_dump(mode="json") for request in requested_artifacts]

    return {
        "artifact_type": artifact_type,
        "artifact_uri": artifact_uri,
        "artifact_preview_uri": artifact_preview_uri,
        "artifact_mime_type": artifact_mime_type,
        "artifact_metadata": artifact_metadata,
        "artifact_generation_status": artifact_generation_status,
        "artifact_job_id": artifact_job_id,
        "generated_artifacts": generated_artifacts,
    }

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

class ArtifactStatusResponse(BaseModel):
    post_id: str
    artifact_type: str
    artifact_generation_status: str
    artifact_uri: Optional[str] = None
    artifact_preview_uri: Optional[str] = None
    artifact_mime_type: Optional[str] = None
    artifact_job_id: Optional[str] = None


@router.get("/draft-posts/{post_id}/artifact-status", response_model=ArtifactStatusResponse)
async def get_draft_post_artifact_status(
    post_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> ArtifactStatusResponse:
    """Poll the generation status of a media artifact for a draft post."""
    store = DatabaseDraftBatchStore(db)
    found = await store.find_post(post_id)
    if found is None:
        raise PolicyEnforcementError(
            "Unknown draft post",
            reason="unknown_post_id",
            details={"post_id": post_id},
        )
    _, post = found
    return ArtifactStatusResponse(
        post_id=post_id,
        artifact_type=post.artifact_type or "text",
        artifact_generation_status=post.artifact_generation_status or "not_requested",
        artifact_uri=post.artifact_uri,
        artifact_preview_uri=post.artifact_preview_uri,
        artifact_mime_type=post.artifact_mime_type,
        artifact_job_id=post.artifact_job_id,
    )


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
        if post.artifact_generation_status in {"queued", "running"}:
            raise PolicyEnforcementError(
                "Artifact generation is still in progress",
                reason="artifact_not_ready",
                details={"post_id": post_id, "artifact_generation_status": post.artifact_generation_status},
            )
        try:
            from integrations.social.youtube_client import YouTubeClient

            client = YouTubeClient(
                customer_id=batch.customer_id,
                credential_resolver=DatabaseCredentialResolver(db),
            )
            if post.artifact_type in {"video", "video_audio"} and post.artifact_uri:
                result = await client.post_short(
                    credential_ref=effective_credential_ref,
                    video_url=post.artifact_uri,
                    title=batch.theme,
                    description=post.text,
                )
            else:
                result = await client.post_text(
                    credential_ref=effective_credential_ref,
                    text=post.text,
                    image_url=post.artifact_uri if post.artifact_type == "image" else None,
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
