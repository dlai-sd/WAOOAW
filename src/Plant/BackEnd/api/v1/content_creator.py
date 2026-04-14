"""Content Creator API — unified create → approve → publish endpoints.

POST /api/v1/content-creator/create           → generate content drafts
POST /api/v1/content-creator/posts/{id}/approve → customer approves a post
POST /api/v1/content-creator/posts/{id}/reject  → customer rejects a post
POST /api/v1/content-creator/posts/{id}/publish → publish approved post to YouTube
GET  /api/v1/content-creator/batches           → list draft batches
GET  /api/v1/content-creator/batches/{id}      → get single batch
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.playbook import ArtifactRequest, ChannelName
from core.database import get_db_session, get_read_db_session
from core.exceptions import PolicyEnforcementError
from core.routing import waooaw_router
from services.content_creator_service import ContentCreatorError, ContentCreatorService
from services.draft_batches import DraftBatchRecord, DraftPostRecord

router = waooaw_router(prefix="/content-creator", tags=["content-creator"])


# ── Request / Response schemas ──────────────────────────────────

class CreateContentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    theme: str = Field(..., min_length=1)
    brand_name: str = Field(..., min_length=1)
    hired_instance_id: Optional[str] = None
    campaign_id: Optional[str] = None
    customer_id: Optional[str] = None
    brief_summary: Optional[str] = None
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    channels: Optional[List[ChannelName]] = None
    youtube_credential_ref: Optional[str] = None
    youtube_visibility: str = "private"
    public_release_requested: bool = False
    requested_artifacts: Optional[List[ArtifactRequest]] = None


class ApprovePostRequest(BaseModel):
    approval_id: Optional[str] = None


class ApprovePostResponse(BaseModel):
    post_id: str
    review_status: str
    approval_id: Optional[str] = None


class RejectPostResponse(BaseModel):
    post_id: str
    review_status: str


class PublishPostResponse(BaseModel):
    post_id: str
    execution_status: str
    provider_post_id: Optional[str] = None
    provider_post_url: Optional[str] = None
    channel: Optional[str] = None


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/create", response_model=DraftBatchRecord)
async def create_content(
    body: CreateContentRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DraftBatchRecord:
    """Generate multi-channel content drafts for customer review."""
    service = ContentCreatorService(db)
    try:
        return await service.create_content(
            agent_id=body.agent_id,
            theme=body.theme,
            brand_name=body.brand_name,
            hired_instance_id=body.hired_instance_id,
            campaign_id=body.campaign_id,
            customer_id=body.customer_id,
            brief_summary=body.brief_summary,
            offer=body.offer,
            location=body.location,
            audience=body.audience,
            tone=body.tone,
            language=body.language,
            channels=body.channels,
            youtube_credential_ref=body.youtube_credential_ref,
            youtube_visibility=body.youtube_visibility,
            public_release_requested=body.public_release_requested,
            requested_artifacts=body.requested_artifacts,
        )
    except ContentCreatorError as exc:
        raise PolicyEnforcementError(str(exc), reason=exc.reason, details=exc.details)


@router.get("/batches", response_model=List[DraftBatchRecord])
async def list_batches(
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[DraftBatchRecord]:
    """List content draft batches with optional filters."""
    service = ContentCreatorService(db)
    return await service.list_batches(
        customer_id=customer_id,
        agent_id=agent_id,
        status=status,
        limit=limit,
    )


@router.get("/batches/{batch_id}", response_model=DraftBatchRecord)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> DraftBatchRecord:
    """Get a single draft batch by ID."""
    service = ContentCreatorService(db)
    batch = await service.get_batch(batch_id)
    if batch is None:
        raise PolicyEnforcementError(
            "Unknown batch",
            reason="unknown_batch_id",
            details={"batch_id": batch_id},
        )
    return batch


@router.post("/posts/{post_id}/approve", response_model=ApprovePostResponse)
async def approve_post(
    post_id: str,
    body: ApprovePostRequest = ApprovePostRequest(),
    db: AsyncSession = Depends(get_db_session),
) -> ApprovePostResponse:
    """Customer approves a draft post for publishing."""
    service = ContentCreatorService(db)
    try:
        post = await service.approve_post(post_id, approval_id=body.approval_id)
        return ApprovePostResponse(
            post_id=post.post_id,
            review_status=post.review_status,
            approval_id=post.approval_id,
        )
    except ContentCreatorError as exc:
        raise PolicyEnforcementError(str(exc), reason=exc.reason, details=exc.details)


@router.post("/posts/{post_id}/reject", response_model=RejectPostResponse)
async def reject_post(
    post_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> RejectPostResponse:
    """Customer rejects a draft post."""
    service = ContentCreatorService(db)
    try:
        post = await service.reject_post(post_id)
        return RejectPostResponse(
            post_id=post.post_id,
            review_status=post.review_status,
        )
    except ContentCreatorError as exc:
        raise PolicyEnforcementError(str(exc), reason=exc.reason, details=exc.details)


@router.post("/posts/{post_id}/publish", response_model=PublishPostResponse)
async def publish_post(
    post_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> PublishPostResponse:
    """Publish an approved post to its target platform (YouTube)."""
    service = ContentCreatorService(db)
    try:
        result = await service.publish_post(post_id)
        return PublishPostResponse(**result)
    except ContentCreatorError as exc:
        raise PolicyEnforcementError(str(exc), reason=exc.reason, details=exc.details)
