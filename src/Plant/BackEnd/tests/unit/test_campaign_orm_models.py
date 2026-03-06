"""Unit tests for Campaign ORM models (E1-S1).

Tests that the SQLAlchemy model classes can be instantiated without a live
database connection and that their attributes and defaults are correct.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/unit/test_campaign_orm_models.py -v
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel


# ── Fixtures ──────────────────────────────────────────────────────────────────

BRIEF = {
    "theme": "Hire AI Agents — WAOOAW",
    "start_date": "2026-03-06",
    "duration_days": 7,
    "destinations": [{"destination_type": "simulated"}],
    "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
    "approval_mode": "per_item",
}

COST_ESTIMATE = {
    "total_theme_items": 7,
    "total_posts": 7,
    "llm_calls": 8,
    "cost_per_call_usd": 0.0,
    "total_cost_usd": 0.0,
    "total_cost_inr": 0.0,
    "model_used": "deterministic",
}

DESTINATION = {"destination_type": "simulated"}


# ── CampaignModel ─────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_campaign_model_tablename():
    """E1-S1: CampaignModel.__tablename__ == 'campaigns'."""
    assert CampaignModel.__tablename__ == "campaigns"


@pytest.mark.unit
def test_campaign_model_default_status():
    """E1-S1: CampaignModel defaults to status='draft'."""
    now = datetime.now(timezone.utc)
    campaign = CampaignModel(
        campaign_id="CAM-001",
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
    )
    assert campaign.status == "draft"
    assert campaign.campaign_id == "CAM-001"
    assert campaign.customer_id == "cust-001"
    assert campaign.brief == BRIEF
    assert campaign.cost_estimate == COST_ESTIMATE
    # created_at auto-set
    assert campaign.created_at >= now


@pytest.mark.unit
def test_campaign_model_explicit_status():
    """E1-S1: CampaignModel accepts explicit status."""
    campaign = CampaignModel(
        campaign_id="CAM-002",
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
        status="running",
    )
    assert campaign.status == "running"


@pytest.mark.unit
def test_campaign_model_repr():
    """E1-S1: CampaignModel __repr__ contains expected fields."""
    campaign = CampaignModel(
        campaign_id="CAM-001",
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
    )
    r = repr(campaign)
    assert "CAM-001" in r
    assert "cust-001" in r
    assert "draft" in r


# ── DailyThemeItemModel ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_daily_theme_item_tablename():
    """E1-S1: DailyThemeItemModel.__tablename__ == 'daily_theme_items'."""
    assert DailyThemeItemModel.__tablename__ == "daily_theme_items"


@pytest.mark.unit
def test_daily_theme_item_defaults():
    """E1-S1: DailyThemeItemModel defaults to review_status='pending_review'."""
    item = DailyThemeItemModel(
        theme_item_id="THM-001",
        campaign_id="CAM-001",
        day_number=1,
        scheduled_date=date(2026, 3, 6),
        theme_title="Day 1: AI Agents",
        theme_description="Focus on social proof",
    )
    assert item.theme_item_id == "THM-001"
    assert item.day_number == 1
    assert item.review_status == "pending_review"
    assert item.approved_at is None
    assert item.dimensions == []


@pytest.mark.unit
def test_daily_theme_item_with_dimensions():
    """E1-S1: DailyThemeItemModel stores dimensions list."""
    item = DailyThemeItemModel(
        theme_item_id="THM-002",
        campaign_id="CAM-001",
        day_number=2,
        scheduled_date=date(2026, 3, 7),
        theme_title="Day 2: Social Proof",
        theme_description="Customer testimonials",
        dimensions=["social proof", "education"],
    )
    assert item.dimensions == ["social proof", "education"]


@pytest.mark.unit
def test_daily_theme_item_repr():
    """E1-S1: DailyThemeItemModel __repr__ contains expected fields."""
    item = DailyThemeItemModel(
        theme_item_id="THM-001",
        campaign_id="CAM-001",
        day_number=1,
        scheduled_date=date(2026, 3, 6),
        theme_title="Day 1",
        theme_description="Description",
    )
    r = repr(item)
    assert "THM-001" in r
    assert "CAM-001" in r
    assert "1" in r


# ── ContentPostModel ──────────────────────────────────────────────────────────

@pytest.mark.unit
def test_content_post_tablename():
    """E1-S1: ContentPostModel.__tablename__ == 'content_posts'."""
    assert ContentPostModel.__tablename__ == "content_posts"


@pytest.mark.unit
def test_content_post_defaults():
    """E1-S1: ContentPostModel defaults to correct review/publish status."""
    now = datetime.now(timezone.utc)
    post = ContentPostModel(
        post_id="PST-001",
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hello WAOOAW!",
        scheduled_publish_at=now,
    )
    assert post.post_id == "PST-001"
    assert post.review_status == "pending_review"
    assert post.publish_status == "not_published"
    assert post.publish_receipt is None
    assert post.hashtags == []


@pytest.mark.unit
def test_content_post_with_hashtags():
    """E1-S1: ContentPostModel stores hashtags."""
    now = datetime.now(timezone.utc)
    post = ContentPostModel(
        post_id="PST-002",
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hire AI Agents!",
        scheduled_publish_at=now,
        hashtags=["#AI", "#WAOOAW"],
    )
    assert post.hashtags == ["#AI", "#WAOOAW"]


@pytest.mark.unit
def test_content_post_repr():
    """E1-S1: ContentPostModel __repr__ contains expected fields."""
    now = datetime.now(timezone.utc)
    post = ContentPostModel(
        post_id="PST-001",
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hello",
        scheduled_publish_at=now,
    )
    r = repr(post)
    assert "PST-001" in r
    assert "CAM-001" in r
    assert "pending_review" in r
    assert "not_published" in r
