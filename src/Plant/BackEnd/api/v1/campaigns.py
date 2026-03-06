"""Campaign orchestration API — PLANT-CONTENT-1 Iterations 2 + 3

POST   /campaigns                                              — create campaign + theme list
GET    /campaigns/{campaign_id}                                — get campaign status
GET    /campaigns/{campaign_id}/theme-items                    — list theme items
POST   /campaigns/{campaign_id}/theme-items/approve            — batch approve/reject theme items
PATCH  /campaigns/{campaign_id}/theme-items/{item_id}          — approve/reject single item

POST   /campaigns/{campaign_id}/theme-items/{item_id}/generate-posts — generate posts
GET    /campaigns/{campaign_id}/posts                          — list posts (filterable)
POST   /campaigns/{campaign_id}/posts/approve                  — batch approve posts
PATCH  /campaigns/{campaign_id}/posts/{post_id}                — approve/reject single post

POST   /campaigns/{campaign_id}/posts/{post_id}/publish        — immediately publish one approved post
POST   /campaigns/{campaign_id}/publish-due                    — publish all eligible scheduled posts

Phase 1: in-memory store (same pattern as deliverables_simple.py).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, Field

from agent_mold.skills.content_creator import ContentCreatorSkill
from agent_mold.skills.content_models import (
    Campaign,
    CampaignBrief,
    CampaignStatus,
    ContentPost,
    CostEstimate,
    DailyThemeItem,
    PostGeneratorInput,
    PublishInput,
    PublishStatus,
    PublishReceipt,
    ReviewStatus,
    estimate_cost,
)
from agent_mold.skills.publisher_engine import default_engine
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/campaigns", tags=["campaigns"])

# ─── In-memory stores (Phase 1) ───────────────────────────────────────────────
_campaigns: dict[str, Campaign] = {}
_theme_items: dict[str, dict[str, DailyThemeItem]] = {}  # campaign_id → {item_id → item}
_posts: dict[str, dict[str, ContentPost]] = {}  # campaign_id → {post_id → post}


# ─── Auth helper ──────────────────────────────────────────────────────────────

def _require_auth(authorization: Optional[str]) -> None:
    """Raise 401 if Authorization header is absent."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Request / Response schemas ───────────────────────────────────────────────

class CreateCampaignRequest(BaseModel):
    hired_instance_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    brief: CampaignBrief


class CreateCampaignResponse(BaseModel):
    campaign: Campaign
    theme_items: list[DailyThemeItem]
    cost_estimate: CostEstimate
    message: str


class ApproveThemeItemsRequest(BaseModel):
    item_ids: list[str] = Field(default_factory=list,
        description="IDs to approve/reject. Empty = all pending items (batch mode).")
    decision: Literal["approved", "rejected"]
    notes: str = ""


class ThemeItemPatchRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = ""


class ApprovePostsRequest(BaseModel):
    post_ids: list[str] = Field(default_factory=list,
        description="IDs to approve/reject. Empty = all pending posts (batch mode).")
    decision: Literal["approved", "rejected"]
    notes: str = ""


class PostPatchRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = ""


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _all_themes_approved(campaign_id: str) -> bool:
    items = _theme_items.get(campaign_id, {})
    if not items:
        return False
    return all(item.review_status == ReviewStatus.APPROVED for item in items.values())


# ─── Epic E3 — Campaign CRUD + theme list ─────────────────────────────────────

@router.post("", response_model=CreateCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CreateCampaignRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> CreateCampaignResponse:
    """Create a campaign from a brief. Returns cost estimate + full daily theme list."""
    _require_auth(authorization)

    model_used = "grok-3-latest" if os.getenv("EXECUTOR_BACKEND", "deterministic").lower() == "grok" else "deterministic"
    cost = estimate_cost(body.brief, model_used=model_used)

    campaign = Campaign(
        hired_instance_id=body.hired_instance_id,
        customer_id=body.customer_id,
        brief=body.brief,
        cost_estimate=cost,
    )

    skill = ContentCreatorSkill()
    creator_output = skill.generate_theme_list(campaign)
    theme_items_list = creator_output.theme_items

    _campaigns[campaign.campaign_id] = campaign
    _theme_items[campaign.campaign_id] = {item.theme_item_id: item for item in theme_items_list}

    logger.info("Campaign created: campaign_id=%s customer_id=<masked>", campaign.campaign_id)

    return CreateCampaignResponse(
        campaign=campaign,
        theme_items=theme_items_list,
        cost_estimate=cost,
        message="Campaign created. Review and approve theme items to proceed.",
    )


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Campaign:
    """Get campaign status and metadata."""
    _require_auth(authorization)
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


@router.get("/{campaign_id}/theme-items", response_model=list[DailyThemeItem])
async def list_theme_items(
    campaign_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> list[DailyThemeItem]:
    """List all theme items for a campaign, ordered by day_number."""
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    items = _theme_items.get(campaign_id, {})
    return sorted(items.values(), key=lambda x: x.day_number)


@router.post("/{campaign_id}/theme-items/approve", response_model=list[DailyThemeItem])
async def approve_theme_items(
    campaign_id: str,
    body: ApproveThemeItemsRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> list[DailyThemeItem]:
    """Approve or reject theme items. Empty item_ids = all pending (batch mode)."""
    _require_auth(authorization)
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    items_map = _theme_items.get(campaign_id, {})
    now = datetime.now(timezone.utc)

    targets = body.item_ids if body.item_ids else [
        item_id for item_id, item in items_map.items()
        if item.review_status == ReviewStatus.PENDING_REVIEW
    ]

    affected: list[DailyThemeItem] = []
    for item_id in targets:
        item = items_map.get(item_id)
        if not item:
            continue
        item.review_status = ReviewStatus(body.decision)
        if body.decision == "approved":
            item.approved_at = now
        affected.append(item)

    # Transition campaign status when all themes are approved
    if _all_themes_approved(campaign_id):
        campaign.status = CampaignStatus.THEME_APPROVED
        campaign.updated_at = now
        _campaigns[campaign_id] = campaign

    return affected


@router.patch("/{campaign_id}/theme-items/{item_id}", response_model=DailyThemeItem)
async def patch_theme_item(
    campaign_id: str,
    item_id: str,
    body: ThemeItemPatchRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> DailyThemeItem:
    """Approve or reject a single theme item."""
    _require_auth(authorization)
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    items_map = _theme_items.get(campaign_id, {})
    item = items_map.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme item not found.")

    now = datetime.now(timezone.utc)
    item.review_status = ReviewStatus(body.decision)
    if body.decision == "approved":
        item.approved_at = now

    # Transition campaign status when all themes are approved
    if _all_themes_approved(campaign_id):
        campaign.status = CampaignStatus.THEME_APPROVED
        campaign.updated_at = now
        _campaigns[campaign_id] = campaign

    return item


# ─── Epic E4 — Post generation + post approval ────────────────────────────────

@router.post(
    "/{campaign_id}/theme-items/{item_id}/generate-posts",
    response_model=list[ContentPost],
    status_code=status.HTTP_201_CREATED,
)
async def generate_posts_for_theme_item(
    campaign_id: str,
    item_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> list[ContentPost]:
    """Generate platform-specific posts for one approved theme item."""
    _require_auth(authorization)
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    items_map = _theme_items.get(campaign_id, {})
    theme_item = items_map.get(item_id)
    if not theme_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme item not found.")

    if theme_item.review_status != ReviewStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Theme item must be approved before generating posts.",
        )

    skill = ContentCreatorSkill()
    inp = PostGeneratorInput(campaign=campaign, theme_item=theme_item)
    post_output = skill.generate_posts_for_theme(inp)

    posts_map = _posts.setdefault(campaign_id, {})
    for post in post_output.posts:
        posts_map[post.post_id] = post

    logger.info(
        "Posts generated: campaign_id=%s theme_item_id=%s count=%d",
        campaign_id, item_id, len(post_output.posts),
    )

    return post_output.posts


@router.get("/{campaign_id}/posts", response_model=list[ContentPost])
async def list_posts(
    campaign_id: str,
    destination_type: Optional[str] = None,
    review_status: Optional[str] = None,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> list[ContentPost]:
    """List all posts for a campaign. Filterable by destination_type and review_status."""
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    posts = list(_posts.get(campaign_id, {}).values())
    if destination_type:
        posts = [p for p in posts if p.destination.destination_type == destination_type]
    if review_status:
        posts = [p for p in posts if p.review_status.value == review_status]

    return sorted(posts, key=lambda p: (p.created_at, p.post_id))


@router.post("/{campaign_id}/posts/approve", response_model=list[ContentPost])
async def approve_posts(
    campaign_id: str,
    body: ApprovePostsRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> list[ContentPost]:
    """Approve or reject posts. Empty post_ids = all pending (batch mode)."""
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    posts_map = _posts.get(campaign_id, {})
    now = datetime.now(timezone.utc)

    targets = body.post_ids if body.post_ids else [
        post_id for post_id, post in posts_map.items()
        if post.review_status == ReviewStatus.PENDING_REVIEW
    ]

    affected: list[ContentPost] = []
    for post_id in targets:
        post = posts_map.get(post_id)
        if not post:
            continue
        post.review_status = ReviewStatus(body.decision)
        post.updated_at = now
        affected.append(post)

    return affected


@router.patch("/{campaign_id}/posts/{post_id}", response_model=ContentPost)
async def patch_post(
    campaign_id: str,
    post_id: str,
    body: PostPatchRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ContentPost:
    """Approve or reject a single post."""
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    posts_map = _posts.get(campaign_id, {})
    post = posts_map.get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    now = datetime.now(timezone.utc)
    post.review_status = ReviewStatus(body.decision)
    post.updated_at = now

    return post


# ─── Epic E6 — Publish routes ─────────────────────────────────────────────────

class PublishReceiptResponse(BaseModel):
    receipt: PublishReceipt
    message: str


class PublishDueResponse(BaseModel):
    published_count: int
    receipts: list[PublishReceipt]


@router.post(
    "/{campaign_id}/posts/{post_id}/publish",
    response_model=PublishReceiptResponse,
)
async def publish_post(
    campaign_id: str,
    post_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> PublishReceiptResponse:
    """Immediately publish one approved post via the default PublisherEngine.

    Returns 409 if the post is not approved or is already published.
    """
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    posts_map = _posts.get(campaign_id, {})
    post = posts_map.get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    if post.review_status != ReviewStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Post must be approved before publishing.",
        )

    if post.publish_status == PublishStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Post is already published.",
        )

    inp = PublishInput(post=post)
    receipt = default_engine.publish(inp)

    now = datetime.now(timezone.utc)
    if receipt.success:
        post.publish_status = PublishStatus.PUBLISHED
        post.publish_receipt = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
    else:
        post.publish_status = PublishStatus.FAILED
        post.publish_receipt = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
    post.updated_at = now

    logger.info(
        "Post publish attempt: campaign_id=%s post_id=%s success=%s",
        campaign_id, post_id, receipt.success,
    )

    return PublishReceiptResponse(
        receipt=receipt,
        message="Published successfully." if receipt.success else f"Publish failed: {receipt.error}",
    )


@router.post(
    "/{campaign_id}/publish-due",
    response_model=PublishDueResponse,
)
async def publish_due(
    campaign_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> PublishDueResponse:
    """Publish all approved posts whose scheduled_publish_at <= now UTC.

    Used by scheduler/cron. Returns count of posts published.
    """
    _require_auth(authorization)
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    now = datetime.now(timezone.utc)
    posts_map = _posts.get(campaign_id, {})

    eligible = [
        post for post in posts_map.values()
        if (
            post.review_status == ReviewStatus.APPROVED
            and post.publish_status == PublishStatus.NOT_PUBLISHED
            and post.scheduled_publish_at <= now
        )
    ]

    receipts: list[PublishReceipt] = []
    for post in eligible:
        inp = PublishInput(post=post)
        receipt = default_engine.publish(inp)
        if receipt.success:
            post.publish_status = PublishStatus.PUBLISHED
        else:
            post.publish_status = PublishStatus.FAILED
        post.publish_receipt = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
        post.updated_at = now
        receipts.append(receipt)

    logger.info(
        "publish-due: campaign_id=%s eligible=%d published=%d",
        campaign_id, len(eligible), sum(1 for r in receipts if r.success),
    )

    return PublishDueResponse(published_count=len(receipts), receipts=receipts)
