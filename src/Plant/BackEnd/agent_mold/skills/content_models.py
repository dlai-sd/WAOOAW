"""Content creator and publisher — shared campaign models.

All skills, API routes, and adapters import from here.
Do NOT redefine ChannelName or CanonicalMessage — import from playbook.py.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from agent_mold.skills.playbook import ChannelName


# ─── Enums ────────────────────────────────────────────────────────────────────

class ApprovalMode(str, Enum):
    PER_ITEM = "per_item"   # customer approves each item individually
    BATCH = "batch"          # customer approves a list in one call
    AUTO = "auto"            # no customer review required


class ReviewStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    THEME_APPROVED = "theme_approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class PublishStatus(str, Enum):
    NOT_PUBLISHED = "not_published"
    PUBLISHED = "published"
    FAILED = "failed"


class CampaignWorkflowState(str, Enum):
    BRIEF_CAPTURED = "brief_captured"
    DRAFT_READY_FOR_REVIEW = "draft_ready_for_review"
    AWAITING_CUSTOMER_APPROVAL = "awaiting_customer_approval"
    APPROVED_FOR_UPLOAD = "approved_for_upload"


# ─── Campaign Brief (customer input) ─────────────────────────────────────────

class DestinationRef(BaseModel):
    """Reference to a publish destination. Adapter registered by destination_type."""
    destination_type: str = Field(..., min_length=1,
        description="Registered adapter key, e.g. 'simulated', 'linkedin', 'instagram'")
    handle: Optional[str] = Field(None,
        description="Platform handle or channel ID, e.g. '@waooaw' or 'UCxxx'")
    metadata: Dict[str, Any] = Field(default_factory=dict,
        description="Adapter-specific config, e.g. page_id, access_token_ref")


class PostingSchedule(BaseModel):
    """Defines how often to post within a campaign."""
    times_per_day: int = Field(1, ge=1, le=24,
        description="Number of posts per day per platform")
    preferred_hours_utc: List[int] = Field(
        default_factory=lambda: [9],
        description="Preferred UTC hours for posting, e.g. [9, 17]"
    )

    @validator("preferred_hours_utc", each_item=True)
    def _valid_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError(f"Hour must be 0-23, got {v}")
        return v


class PostingCadence(BaseModel):
    """Structured cadence captured during Theme Discovery."""

    posts_per_week: int = Field(1, ge=1, le=21)
    preferred_days: List[str] = Field(default_factory=list)
    preferred_hours_utc: List[int] = Field(default_factory=lambda: [9])

    @validator("preferred_hours_utc", each_item=True)
    def _valid_cadence_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError(f"Hour must be 0-23, got {v}")
        return v


class ThemeDiscoveryChannelIntent(BaseModel):
    """Customer intent for the first live publishing channel."""

    primary_destination: str = Field(..., min_length=1)
    supported_live_destinations: List[str] = Field(default_factory=lambda: ["youtube"], min_length=1)
    content_formats: List[str] = Field(default_factory=list)
    call_to_action: str = Field("", description="Primary CTA the content should drive")


class SuccessMetric(BaseModel):
    """Customer-facing definition of success for the campaign."""

    name: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class ThemeDiscoveryBrief(BaseModel):
    """Structured marketing brief captured before content creation begins."""

    business_background: str = Field(..., min_length=3)
    objective: str = Field(..., min_length=3)
    industry: str = Field(..., min_length=2)
    locality: str = Field(..., min_length=2)
    target_audience: str = Field(..., min_length=3)
    persona: str = Field(..., min_length=3)
    tone: str = Field(..., min_length=2)
    offer: str = Field(..., min_length=2)
    channel_intent: ThemeDiscoveryChannelIntent
    posting_cadence: PostingCadence = Field(default_factory=PostingCadence)
    success_metrics: List[SuccessMetric] = Field(default_factory=list)


class CampaignBriefSummary(BaseModel):
    """Compact summary of the structured brief for CP, PP, and mobile surfaces."""

    summary_text: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    offer: str = Field("")
    primary_destination: str = Field(..., min_length=1)
    cadence_text: str = Field(..., min_length=1)
    success_metrics: List[str] = Field(default_factory=list)


class DraftDeliverableSummary(BaseModel):
    """Small runtime view of reviewable draft deliverables."""

    deliverable_id: str = Field(..., min_length=1)
    theme_item_id: str = Field(..., min_length=1)
    destination_type: str = Field(..., min_length=1)
    review_status: ReviewStatus
    publish_status: PublishStatus


class CampaignApprovalState(BaseModel):
    """Roll-up of approval progress for the campaign runtime."""

    pending_review_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0


class CampaignBrief(BaseModel):
    """Customer-submitted campaign brief. Immutable after creation."""
    theme: str = Field(..., min_length=3,
        description="Campaign master theme, e.g. 'Hire AI Agents — WAOOAW'")
    start_date: date = Field(...,
        description="ISO date for first post, e.g. '2026-03-06'")
    duration_days: int = Field(..., ge=1, le=365,
        description="Total campaign length in days")
    destinations: List[DestinationRef] = Field(..., min_length=1,
        description="One or more publish destinations")
    schedule: PostingSchedule = Field(default_factory=PostingSchedule)
    brand_name: str = Field("", description="Brand name for content personalisation")
    audience: str = Field("", description="Target audience description")
    tone: str = Field("professional", description="Content tone, e.g. 'inspiring', 'casual'")
    language: str = Field("en", description="ISO 639-1 language code")
    approval_mode: ApprovalMode = Field(ApprovalMode.PER_ITEM)
    theme_discovery: Optional[ThemeDiscoveryBrief] = Field(
        None,
        description="Structured Theme Discovery brief used by the Digital Marketing Agent",
    )
    additional_context: str = Field("",
        description="Free-text extra instructions for the content creator")


# ─── Cost Estimate ────────────────────────────────────────────────────────────

class CostEstimate(BaseModel):
    total_theme_items: int
    total_posts: int
    llm_calls: int
    cost_per_call_usd: float
    total_cost_usd: float
    total_cost_inr: float
    model_used: str
    note: str = ""


def estimate_cost(brief: CampaignBrief, model_used: str = "deterministic") -> CostEstimate:
    """Pure function — no I/O. Called before any LLM request is made.

    Cost is zero for deterministic mode and Grok free-tier models.
    Update cost_per_call_usd when switching to paid models.
    """
    total_theme_items = brief.duration_days
    posts_per_day = brief.schedule.times_per_day * len(brief.destinations)
    total_posts = total_theme_items * posts_per_day
    # 1 LLM call for full theme list + 1 LLM call per post
    llm_calls = 1 + total_posts

    # Pricing table — update when model changes
    COST_TABLE: Dict[str, float] = {
        "deterministic": 0.0,
        "grok-3-latest": 0.0,      # free tier as of 2026-03
        "grok-2-latest": 0.0,      # free tier as of 2026-03
    }
    cost_per_call = COST_TABLE.get(model_used, 0.001)  # default $0.001 for unknown models
    total_usd = llm_calls * cost_per_call
    # INR conversion — update via env var COST_USD_TO_INR (default 84)
    usd_to_inr = float(os.getenv("COST_USD_TO_INR", "84"))
    total_inr = total_usd * usd_to_inr

    return CostEstimate(
        total_theme_items=total_theme_items,
        total_posts=total_posts,
        llm_calls=llm_calls,
        cost_per_call_usd=cost_per_call,
        total_cost_usd=total_usd,
        total_cost_inr=total_inr,
        model_used=model_used,
        note="₹0 — Grok free tier" if cost_per_call == 0.0 else "",
    )


# ─── Campaign + Theme Items + Posts ───────────────────────────────────────────

class Campaign(BaseModel):
    campaign_id: str = Field(default_factory=lambda: str(uuid4()))
    hired_instance_id: str
    customer_id: str
    brief: CampaignBrief
    cost_estimate: CostEstimate
    status: CampaignStatus = CampaignStatus.DRAFT
    workflow_state: CampaignWorkflowState = CampaignWorkflowState.BRIEF_CAPTURED
    brief_summary: Optional[CampaignBriefSummary] = None
    draft_deliverables: List[DraftDeliverableSummary] = Field(default_factory=list)
    approval_state: CampaignApprovalState = Field(default_factory=CampaignApprovalState)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DailyThemeItem(BaseModel):
    theme_item_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    day_number: int = Field(..., ge=1)
    scheduled_date: date
    theme_title: str
    theme_description: str
    dimensions: List[str] = Field(default_factory=list,
        description="Content angles for this day, e.g. ['social proof', 'education']")
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    approved_at: Optional[datetime] = None


class ContentPost(BaseModel):
    post_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    theme_item_id: str
    destination: DestinationRef
    content_text: str
    hashtags: List[str] = Field(default_factory=list)
    scheduled_publish_at: datetime
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    publish_status: PublishStatus = PublishStatus.NOT_PUBLISHED
    publish_receipt: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Skill I/O contracts ──────────────────────────────────────────────────────

class ContentCreatorInput(BaseModel):
    """Input to the ContentCreatorSkill."""
    campaign: Campaign


class ContentCreatorOutput(BaseModel):
    """Output of the ContentCreatorSkill — theme list for the full campaign."""
    campaign_id: str
    theme_items: List[DailyThemeItem]
    cost_estimate: CostEstimate


class PostGeneratorInput(BaseModel):
    """Input to generate platform-specific posts for one approved theme item."""
    campaign: Campaign
    theme_item: DailyThemeItem


class PostGeneratorOutput(BaseModel):
    """Output — one ContentPost per destination, for one theme item."""
    theme_item_id: str
    posts: List[ContentPost]


class PublishInput(BaseModel):
    """Input to the PublisherEngine for one approved post."""
    post: ContentPost
    credential_ref: Optional[str] = Field(None,
        description="Secret Manager key for platform OAuth token, if required")


class PublishReceipt(BaseModel):
    post_id: str
    destination_type: str
    success: bool
    platform_post_id: Optional[str] = None
    published_at: Optional[datetime] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
