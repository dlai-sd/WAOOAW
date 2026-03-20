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
from datetime import date, timedelta
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Literal, Optional

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.content_creator import ContentCreatorSkill
from agent_mold.skills.content_models import (
    Campaign,
    CampaignBrief,
    CampaignBriefSummary,
    CampaignStatus,
    CampaignWorkflowState,
    CampaignApprovalState,
    ContentPost,
    CostEstimate,
    DailyThemeItem,
    DraftDeliverableSummary,
    PostGeneratorInput,
    PublishInput,
    PublishStatus,
    PublishReceipt,
    ReviewStatus,
    estimate_cost,
)
from agent_mold.skills.publisher_engine import default_engine
from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel
from repositories.campaign_repository import CampaignRepository

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/campaigns", tags=["campaigns"])

# ─── Feature flag ─────────────────────────────────────────────────────────────
# "memory"  → existing in-memory dicts (default, backward-compatible)
# "db"      → PostgreSQL via CampaignRepository (requires migration 026)
CAMPAIGN_PERSISTENCE_MODE = os.getenv("CAMPAIGN_PERSISTENCE_MODE", "db").lower()


async def _get_write_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield a write DB session when CAMPAIGN_PERSISTENCE_MODE=db; else yield None."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_db_session():
        yield session


async def _get_read_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield a read-replica session when CAMPAIGN_PERSISTENCE_MODE=db; else yield None."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_read_db_session():
        yield session


# ─── ORM → Pydantic converters ────────────────────────────────────────────────

def _orm_campaign_to_pydantic(m: CampaignModel) -> Campaign:
    payload = {
        "campaign_id":       m.campaign_id,
        "hired_instance_id": m.hired_instance_id,
        "customer_id":       m.customer_id,
        "brief":             m.brief,
        "cost_estimate":     m.cost_estimate,
        "status":            m.status,
        "created_at":        m.created_at,
        "updated_at":        m.updated_at,
    }
    if m.workflow_state:
        payload["workflow_state"] = m.workflow_state
    if isinstance(m.brief_summary, dict) and m.brief_summary.get("summary_text"):
        payload["brief_summary"] = m.brief_summary
    if m.approval_state:
        payload["approval_state"] = m.approval_state
    if m.draft_deliverables:
        payload["draft_deliverables"] = m.draft_deliverables
    return Campaign.model_validate(payload)


def _orm_theme_item_to_pydantic(m: DailyThemeItemModel) -> DailyThemeItem:
    return DailyThemeItem.model_validate({
        "theme_item_id":     m.theme_item_id,
        "campaign_id":       m.campaign_id,
        "day_number":        m.day_number,
        "scheduled_date":    m.scheduled_date,
        "theme_title":       m.theme_title,
        "theme_description": m.theme_description,
        "dimensions":        m.dimensions or [],
        "review_status":     m.review_status,
        "approved_at":       m.approved_at,
    })


def _orm_post_to_pydantic(m: ContentPostModel) -> ContentPost:
    destination = dict(m.destination or {})
    metadata = dict(destination.get("metadata") or {})
    if m.approval_id is not None:
        metadata["approval_id"] = m.approval_id
    if m.credential_ref is not None:
        metadata["credential_ref"] = m.credential_ref
    metadata["visibility"] = m.visibility
    metadata["public_release_requested"] = str(m.public_release_requested).lower() == "true"
    destination["metadata"] = metadata
    return ContentPost.model_validate({
        "post_id":              m.post_id,
        "campaign_id":          m.campaign_id,
        "theme_item_id":        m.theme_item_id,
        "destination":          destination,
        "content_text":         m.content_text,
        "hashtags":             m.hashtags or [],
        "scheduled_publish_at": m.scheduled_publish_at,
        "review_status":        m.review_status,
        "publish_status":       m.publish_status,
        "publish_receipt":      m.publish_receipt,
        "created_at":           m.created_at,
        "updated_at":           m.updated_at,
    })


def _build_brief_summary(brief: CampaignBrief) -> CampaignBriefSummary:
    theme_discovery = brief.theme_discovery
    if theme_discovery is not None:
        cadence = theme_discovery.posting_cadence
        cadence_text = f"{cadence.posts_per_week} posts/week"
        success_metrics = [f"{metric.name}: {metric.target}" for metric in theme_discovery.success_metrics]
        summary_text = (
            f"{theme_discovery.objective} for {theme_discovery.target_audience} in "
            f"{theme_discovery.locality} using {theme_discovery.channel_intent.primary_destination}."
        )
        return CampaignBriefSummary(
            summary_text=summary_text,
            target_audience=theme_discovery.target_audience,
            offer=theme_discovery.offer,
            primary_destination=theme_discovery.channel_intent.primary_destination,
            cadence_text=cadence_text,
            success_metrics=success_metrics,
        )

    first_destination = brief.destinations[0].destination_type if brief.destinations else "youtube"
    cadence_text = f"{brief.schedule.times_per_day} posts/day"
    summary_text = f"{brief.theme} for {brief.audience or 'the target audience'} on {first_destination}."
    return CampaignBriefSummary(
        summary_text=summary_text,
        target_audience=brief.audience or "General audience",
        offer="",
        primary_destination=first_destination,
        cadence_text=cadence_text,
        success_metrics=[],
    )


def _build_draft_deliverables(posts: list[ContentPost]) -> list[DraftDeliverableSummary]:
    return [
        DraftDeliverableSummary(
            deliverable_id=post.post_id,
            theme_item_id=post.theme_item_id,
            destination_type=post.destination.destination_type,
            review_status=post.review_status,
            publish_status=post.publish_status,
        )
        for post in posts
    ]


def _build_publish_input(post: ContentPost) -> PublishInput:
    metadata = post.destination.metadata or {}
    return PublishInput(
        post=post,
        credential_ref=metadata.get("credential_ref"),
        approval_id=metadata.get("approval_id"),
        visibility=str(metadata.get("visibility") or "private"),
        public_release_requested=bool(metadata.get("public_release_requested", False)),
    )


def _normalize_activation_platforms(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("selected_platforms")
    if not isinstance(raw, list):
        return ["youtube"]
    normalized = [str(item or "").strip().lower() for item in raw]
    deduped = [item for item in normalized if item]
    return deduped or ["youtube"]


def build_campaign_brief_from_activation_payload(payload: dict[str, Any]) -> CampaignBrief:
    """Map Digital Marketing activation data into the shared CampaignBrief model."""
    induction = dict(payload.get("induction") or {})
    theme_plan = dict(payload.get("theme_plan") or {})
    schedule_payload = dict(payload.get("schedule") or {})

    selected_platforms = _normalize_activation_platforms(payload)

    raw_hours = schedule_payload.get("preferred_hours_utc")
    hours_input = raw_hours if isinstance(raw_hours, list) else [9]
    preferred_hours: list[int] = []
    for hour in hours_input:
        try:
            preferred_hours.append(int(hour))
        except Exception:
            continue
    preferred_hours = preferred_hours or [9]

    raw_days = schedule_payload.get("preferred_days")
    preferred_days = [str(day) for day in raw_days] if isinstance(raw_days, list) else []

    start_date_raw = str(schedule_payload.get("start_date") or "").strip()
    start_date_value = date.fromisoformat(start_date_raw) if start_date_raw else date.today()

    derived_themes = list(theme_plan.get("derived_themes") or [])
    duration_days = max(len(derived_themes), 1)
    try:
        posts_per_week_value = max(int(schedule_payload.get("posts_per_week") or duration_days), 1)
    except Exception:
        posts_per_week_value = max(duration_days, 1)

    offerings = induction.get("offerings_services")
    offer_text = (
        ", ".join(str(item).strip() for item in offerings if str(item).strip())
        if isinstance(offerings, list)
        else str(offerings or "").strip()
    )

    return CampaignBrief(
        theme=str(theme_plan.get("master_theme") or "Digital marketing activation").strip() or "Digital marketing activation",
        start_date=start_date_value,
        duration_days=duration_days,
        destinations=[
            {
                "destination_type": platform,
                "metadata": {"activation_step": "digital_marketing_activation"},
            }
            for platform in selected_platforms
        ],
        schedule={
            "times_per_day": 1,
            "preferred_hours_utc": preferred_hours,
        },
        brand_name=str(induction.get("brand_name") or "").strip(),
        audience=str(induction.get("target_audience") or induction.get("brand_name") or "Business audience").strip() or "Business audience",
        tone=str(induction.get("theme") or "professional").strip() or "professional",
        language=str(induction.get("primary_language") or "en").strip() or "en",
        approval_mode="per_item",
        theme_discovery={
            "business_background": str(induction.get("brand_name") or induction.get("business_background") or "Customer activation workspace").strip() or "Customer activation workspace",
            "objective": str(theme_plan.get("master_theme") or "Create a runtime-ready digital marketing campaign").strip(),
            "industry": "Digital Marketing",
            "locality": str(induction.get("location") or "Unknown").strip() or "Unknown",
            "target_audience": str(induction.get("target_audience") or induction.get("brand_name") or "Business audience").strip() or "Business audience",
            "persona": str(induction.get("nickname") or "Digital marketing agent").strip() or "Digital marketing agent",
            "tone": str(induction.get("theme") or "professional").strip() or "professional",
            "offer": offer_text or "Digital marketing services",
            "channel_intent": {
                "primary_destination": selected_platforms[0],
                "supported_live_destinations": selected_platforms,
                "content_formats": [],
                "call_to_action": "",
            },
            "posting_cadence": {
                "posts_per_week": posts_per_week_value,
                "preferred_days": preferred_days,
                "preferred_hours_utc": preferred_hours,
            },
            "success_metrics": [],
        },
        additional_context=str(induction.get("notes") or "").strip(),
    )


def build_theme_items_from_activation_payload(
    *,
    campaign_id: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build persisted theme-item rows from activation theme-plan payload."""
    theme_plan = dict(payload.get("theme_plan") or {})
    schedule_payload = dict(payload.get("schedule") or {})
    derived_themes = list(theme_plan.get("derived_themes") or [])
    start_date_raw = str(schedule_payload.get("start_date") or "").strip()
    start_date_value = date.fromisoformat(start_date_raw) if start_date_raw else date.today()

    if not derived_themes:
        derived_themes = [
            {
                "title": str(theme_plan.get("master_theme") or "Digital marketing theme").strip() or "Digital marketing theme",
                "description": "Draft activation theme.",
                "frequency": "weekly",
            }
        ]

    items: list[dict[str, Any]] = []
    for index, row in enumerate(derived_themes, start=1):
        row_dict = dict(row or {})
        items.append(
            {
                "campaign_id": campaign_id,
                "day_number": index,
                "scheduled_date": start_date_value + timedelta(days=index - 1),
                "theme_title": str(row_dict.get("title") or f"Theme {index}").strip() or f"Theme {index}",
                "theme_description": str(row_dict.get("description") or "").strip() or "Derived campaign theme.",
                "dimensions": [str(row_dict.get("frequency") or "").strip()] if str(row_dict.get("frequency") or "").strip() else [],
            }
        )
    return items


def _build_approval_state(posts: list[ContentPost]) -> CampaignApprovalState:
    pending = sum(1 for post in posts if post.review_status == ReviewStatus.PENDING_REVIEW)
    approved = sum(1 for post in posts if post.review_status == ReviewStatus.APPROVED)
    rejected = sum(1 for post in posts if post.review_status == ReviewStatus.REJECTED)
    return CampaignApprovalState(
        pending_review_count=pending,
        approved_count=approved,
        rejected_count=rejected,
    )


def _derive_workflow_state(
    theme_items: list[DailyThemeItem],
    posts: list[ContentPost],
) -> CampaignWorkflowState:
    if not theme_items and not posts:
        return CampaignWorkflowState.BRIEF_CAPTURED
    if posts and all(post.review_status == ReviewStatus.APPROVED for post in posts):
        return CampaignWorkflowState.APPROVED_FOR_UPLOAD
    if posts:
        return CampaignWorkflowState.AWAITING_CUSTOMER_APPROVAL
    return CampaignWorkflowState.DRAFT_READY_FOR_REVIEW


def _enrich_campaign_runtime(
    campaign: Campaign,
    *,
    theme_items: list[DailyThemeItem],
    posts: list[ContentPost],
) -> Campaign:
    return campaign.model_copy(
        update={
            "workflow_state": _derive_workflow_state(theme_items, posts),
            "brief_summary": _build_brief_summary(campaign.brief),
            "draft_deliverables": _build_draft_deliverables(posts),
            "approval_state": _build_approval_state(posts),
        }
    )


async def _persist_campaign_runtime(repo: CampaignRepository, campaign_id: str) -> Campaign:
    orm_campaign = await repo.get_campaign_by_id(campaign_id)
    if orm_campaign is None:
        raise ValueError(f"Campaign {campaign_id!r} not found")
    orm_theme_items = await repo.list_theme_items_by_campaign(campaign_id)
    orm_posts = await repo.list_posts_by_campaign(campaign_id)
    campaign = _enrich_campaign_runtime(
        _orm_campaign_to_pydantic(orm_campaign),
        theme_items=[_orm_theme_item_to_pydantic(item) for item in orm_theme_items],
        posts=[_orm_post_to_pydantic(post) for post in orm_posts],
    )
    await repo.update_campaign_runtime(
        campaign_id,
        workflow_state=campaign.workflow_state.value,
        brief_summary=campaign.brief_summary.model_dump(mode="json") if campaign.brief_summary else {},
        approval_state=campaign.approval_state.model_dump(mode="json"),
        draft_deliverables=[draft.model_dump(mode="json") for draft in campaign.draft_deliverables],
    )
    return campaign

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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> CreateCampaignResponse:
    """Create a campaign from a brief. Returns cost estimate + full daily theme list."""
    _require_auth(authorization)

    model_used = "grok-3-latest" if os.getenv("EXECUTOR_BACKEND", "deterministic").lower() == "grok" else "deterministic"
    cost = estimate_cost(body.brief, model_used=model_used)

    if db is not None:
        repo = CampaignRepository(db)
        campaign_pydantic = Campaign(
            hired_instance_id=body.hired_instance_id,
            customer_id=body.customer_id,
            brief=body.brief,
            cost_estimate=cost,
        )
        orm_campaign = await repo.create_campaign(
            hired_instance_id=body.hired_instance_id,
            customer_id=body.customer_id,
            brief=body.brief.model_dump(mode="json"),
            cost_estimate=cost.model_dump(mode="json"),
            campaign_id=campaign_pydantic.campaign_id,
        )
        campaign = _orm_campaign_to_pydantic(orm_campaign)
        skill = ContentCreatorSkill()
        creator_output = skill.generate_theme_list(campaign)
        theme_items_list = creator_output.theme_items
        for item in theme_items_list:
            await repo.create_theme_item(
                campaign_id=item.campaign_id,
                day_number=item.day_number,
                scheduled_date=item.scheduled_date,
                theme_title=item.theme_title,
                theme_description=item.theme_description,
                dimensions=item.dimensions,
                theme_item_id=item.theme_item_id,
            )
        campaign = await _persist_campaign_runtime(repo, campaign.campaign_id)
        await db.commit()
        logger.info("Campaign created: campaign_id=%s customer_id=<masked>", campaign.campaign_id)
        return CreateCampaignResponse(
            campaign=campaign,
            theme_items=theme_items_list,
            cost_estimate=cost,
            message="Campaign created. Review and approve theme items to proceed.",
        )

    # --- memory mode (existing code, UNCHANGED) ---
    campaign = Campaign(
        hired_instance_id=body.hired_instance_id,
        customer_id=body.customer_id,
        brief=body.brief,
        cost_estimate=cost,
    )
    campaign = _enrich_campaign_runtime(campaign, theme_items=[], posts=[])

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
    db: Optional[AsyncSession] = Depends(_get_read_db),
) -> Campaign:
    """Get campaign status and metadata."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        orm_campaign = await repo.get_campaign_by_id(campaign_id)
        if not orm_campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        return _orm_campaign_to_pydantic(orm_campaign)
    # --- memory mode ---
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return _enrich_campaign_runtime(
        campaign,
        theme_items=list(_theme_items.get(campaign_id, {}).values()),
        posts=list(_posts.get(campaign_id, {}).values()),
    )


@router.get("/{campaign_id}/theme-items", response_model=list[DailyThemeItem])
async def list_theme_items(
    campaign_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Optional[AsyncSession] = Depends(_get_read_db),
) -> list[DailyThemeItem]:
    """List all theme items for a campaign, ordered by day_number."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_items = await repo.list_theme_items_by_campaign(campaign_id)
        return [_orm_theme_item_to_pydantic(m) for m in orm_items]
    # --- memory mode ---
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    items = _theme_items.get(campaign_id, {})
    return sorted(items.values(), key=lambda x: x.day_number)


@router.post("/{campaign_id}/theme-items/approve", response_model=list[DailyThemeItem])
async def approve_theme_items(
    campaign_id: str,
    body: ApproveThemeItemsRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> list[DailyThemeItem]:
    """Approve or reject theme items. Empty item_ids = all pending (batch mode)."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_items = await repo.list_theme_items_by_campaign(campaign_id)
        now = datetime.now(timezone.utc)
        targets = body.item_ids if body.item_ids else [
            item.theme_item_id for item in orm_items
            if item.review_status == ReviewStatus.PENDING_REVIEW.value
        ]
        affected: list[DailyThemeItem] = []
        for item_id in targets:
            try:
                updated = await repo.update_theme_item_review_status(
                    item_id,
                    body.decision,
                    approved_at=now if body.decision == "approved" else None,
                )
                affected.append(_orm_theme_item_to_pydantic(updated))
            except ValueError:
                continue
        # Transition campaign status when all themes approved
        refreshed = await repo.list_theme_items_by_campaign(campaign_id)
        if refreshed and all(item.review_status == ReviewStatus.APPROVED.value for item in refreshed):
            await repo.update_campaign_status(campaign_id, CampaignStatus.THEME_APPROVED.value)
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        return affected

    # --- memory mode (existing code, UNCHANGED) ---
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> DailyThemeItem:
    """Approve or reject a single theme item."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        now = datetime.now(timezone.utc)
        try:
            updated = await repo.update_theme_item_review_status(
                item_id,
                body.decision,
                approved_at=now if body.decision == "approved" else None,
            )
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme item not found.")
        # Transition campaign status when all themes approved
        refreshed = await repo.list_theme_items_by_campaign(campaign_id)
        if refreshed and all(item.review_status == ReviewStatus.APPROVED.value for item in refreshed):
            await repo.update_campaign_status(campaign_id, CampaignStatus.THEME_APPROVED.value)
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        return _orm_theme_item_to_pydantic(updated)

    # --- memory mode (existing code, UNCHANGED) ---
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> list[ContentPost]:
    """Generate platform-specific posts for one approved theme item."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        orm_campaign = await repo.get_campaign_by_id(campaign_id)
        if not orm_campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_item = await repo.get_theme_item_by_id(item_id)
        if not orm_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme item not found.")
        if orm_item.review_status != ReviewStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Theme item must be approved before generating posts.",
            )
        campaign = _orm_campaign_to_pydantic(orm_campaign)
        theme_item = _orm_theme_item_to_pydantic(orm_item)
        skill = ContentCreatorSkill()
        inp = PostGeneratorInput(campaign=campaign, theme_item=theme_item)
        post_output = skill.generate_posts_for_theme(inp)
        for post in post_output.posts:
            metadata = post.destination.metadata or {}
            await repo.create_post(
                campaign_id=post.campaign_id,
                theme_item_id=post.theme_item_id,
                destination=post.destination.model_dump(mode="json"),
                content_text=post.content_text,
                scheduled_publish_at=post.scheduled_publish_at,
                hashtags=post.hashtags,
                post_id=post.post_id,
                approval_id=metadata.get("approval_id"),
                credential_ref=metadata.get("credential_ref"),
                visibility=str(metadata.get("visibility") or "private"),
                public_release_requested=bool(metadata.get("public_release_requested", False)),
            )
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        logger.info(
            "Posts generated: campaign_id=%s theme_item_id=%s count=%d",
            campaign_id, item_id, len(post_output.posts),
        )
        return post_output.posts

    # --- memory mode (existing code, UNCHANGED) ---
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
    db: Optional[AsyncSession] = Depends(_get_read_db),
) -> list[ContentPost]:
    """List all posts for a campaign. Filterable by destination_type and review_status."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_posts = await repo.list_posts_by_campaign(campaign_id)
        posts = [_orm_post_to_pydantic(m) for m in orm_posts]
        if destination_type:
            posts = [p for p in posts if p.destination.destination_type == destination_type]
        if review_status:
            posts = [p for p in posts if p.review_status.value == review_status]
        return sorted(posts, key=lambda p: (p.created_at, p.post_id))
    # --- memory mode ---
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> list[ContentPost]:
    """Approve or reject posts. Empty post_ids = all pending (batch mode)."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_posts = await repo.list_posts_by_campaign(campaign_id)
        targets = body.post_ids if body.post_ids else [
            p.post_id for p in orm_posts
            if p.review_status == ReviewStatus.PENDING_REVIEW.value
        ]
        affected: list[ContentPost] = []
        for pid in targets:
            try:
                updated = await repo.update_post_review_status(pid, body.decision)
                affected.append(_orm_post_to_pydantic(updated))
            except ValueError:
                continue
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        return affected

    # --- memory mode (existing code, UNCHANGED) ---
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> ContentPost:
    """Approve or reject a single post."""
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        try:
            updated = await repo.update_post_review_status(post_id, body.decision)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        return _orm_post_to_pydantic(updated)

    # --- memory mode (existing code, UNCHANGED) ---
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> PublishReceiptResponse:
    """Immediately publish one approved post via the default PublisherEngine.

    Returns 409 if the post is not approved or is already published.
    """
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        orm_post = await repo.get_post_by_id(post_id)
        if not orm_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        post = _orm_post_to_pydantic(orm_post)
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
        inp = _build_publish_input(post)
        receipt = default_engine.publish(inp)
        receipt_dict = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
        publish_status_str = PublishStatus.PUBLISHED.value if receipt.success else PublishStatus.FAILED.value
        await repo.update_post_publish_status(post_id, publish_status_str, publish_receipt=receipt_dict)
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        logger.info(
            "Post publish attempt: campaign_id=%s post_id=%s success=%s",
            campaign_id, post_id, receipt.success,
        )
        return PublishReceiptResponse(
            receipt=receipt,
            message="Published successfully." if receipt.success else f"Publish failed: {receipt.error}",
        )

    # --- memory mode (existing code, UNCHANGED) ---
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

    inp = _build_publish_input(post)
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
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> PublishDueResponse:
    """Publish all approved posts whose scheduled_publish_at <= now UTC.

    Used by scheduler/cron. Returns count of posts published.
    """
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        if not await repo.get_campaign_by_id(campaign_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
        now = datetime.now(timezone.utc)
        all_orm_posts = await repo.list_posts_by_campaign(campaign_id)
        eligible_orm = [
            p for p in all_orm_posts
            if (
                p.review_status == ReviewStatus.APPROVED.value
                and p.publish_status == PublishStatus.NOT_PUBLISHED.value
                and p.scheduled_publish_at <= now
            )
        ]
        receipts: list[PublishReceipt] = []
        for orm_post in eligible_orm:
            post = _orm_post_to_pydantic(orm_post)
            inp = _build_publish_input(post)
            receipt = default_engine.publish(inp)
            receipt_dict = receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.dict()
            pub_status = PublishStatus.PUBLISHED.value if receipt.success else PublishStatus.FAILED.value
            await repo.update_post_publish_status(orm_post.post_id, pub_status, publish_receipt=receipt_dict)
            receipts.append(receipt)
        await _persist_campaign_runtime(repo, campaign_id)
        await db.commit()
        logger.info(
            "publish-due: campaign_id=%s eligible=%d published=%d",
            campaign_id, len(eligible_orm), sum(1 for r in receipts if r.success),
        )
        return PublishDueResponse(published_count=len(receipts), receipts=receipts)

    # --- memory mode (existing code, UNCHANGED) ---
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
        inp = _build_publish_input(post)
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
