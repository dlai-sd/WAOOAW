"""Tests for content campaign models and cost estimator (E1-S1)."""
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from agent_mold.skills.content_models import (
    Campaign,
    CampaignBrief,
    CampaignStatus,
    CostEstimate,
    DailyThemeItem,
    DestinationRef,
    PostingSchedule,
    ReviewStatus,
    SuccessMetric,
    ThemeDiscoveryBrief,
    ThemeDiscoveryChannelIntent,
    estimate_cost,
)


def _make_brief(
    duration_days: int = 30,
    times_per_day: int = 1,
    num_destinations: int = 5,
    model_used: str = "grok-3-latest",
) -> CampaignBrief:
    destinations = [
        DestinationRef(destination_type=f"platform_{i}") for i in range(num_destinations)
    ]
    return CampaignBrief(
        theme="Hire AI Agents — WAOOAW",
        start_date=date(2026, 3, 6),
        duration_days=duration_days,
        destinations=destinations,
        schedule=PostingSchedule(times_per_day=times_per_day),
    )


@pytest.mark.unit
def test_estimate_cost_30_days_1_per_day_5_destinations():
    """E1-S1-T1: 30 days, 1×/day, 5 destinations → total_posts==150, total_cost_usd==0.0"""
    brief = _make_brief(duration_days=30, times_per_day=1, num_destinations=5)
    result = estimate_cost(brief, model_used="grok-3-latest")

    assert result.total_posts == 150
    assert result.total_cost_usd == 0.0
    assert result.model_used == "grok-3-latest"


@pytest.mark.unit
def test_estimate_cost_30_days_3_per_day_5_destinations():
    """E1-S1-T2: 30 days, 3×/day, 5 destinations → total_posts==450"""
    brief = _make_brief(duration_days=30, times_per_day=3, num_destinations=5)
    result = estimate_cost(brief, model_used="grok-3-latest")

    assert result.total_posts == 450
    assert result.total_cost_usd == 0.0


@pytest.mark.unit
def test_posting_schedule_invalid_hour_raises_validation_error():
    """E1-S1-T3: preferred_hours_utc=[25] raises ValidationError"""
    with pytest.raises(ValidationError):
        PostingSchedule(preferred_hours_utc=[25])


@pytest.mark.unit
def test_campaign_brief_empty_destinations_raises_validation_error():
    """E1-S1-T4: destinations=[] raises ValidationError (min_length=1)"""
    with pytest.raises(ValidationError):
        CampaignBrief(
            theme="Test Theme",
            start_date=date(2026, 3, 6),
            duration_days=7,
            destinations=[],
        )


@pytest.mark.unit
def test_campaign_and_daily_theme_item_serialize_to_json():
    """E1-S1-T5: Campaign and DailyThemeItem .model_dump_json() (or .json()) serialize without error"""
    brief = _make_brief()
    cost = estimate_cost(brief)
    campaign = Campaign(
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=brief,
        cost_estimate=cost,
    )

    theme_item = DailyThemeItem(
        campaign_id=campaign.campaign_id,
        day_number=1,
        scheduled_date=date(2026, 3, 6),
        theme_title="Day 1: AI Agents",
        theme_description="Focus on social proof",
        dimensions=["social proof"],
    )

    # Pydantic v2 uses model_dump_json(); v1-compat also exposes .json()
    campaign_json = campaign.model_dump_json()
    theme_json = theme_item.model_dump_json()

    assert "campaign_id" in campaign_json
    assert "theme_item_id" in theme_json
    assert campaign.status == CampaignStatus.DRAFT
    assert theme_item.review_status == ReviewStatus.PENDING_REVIEW


@pytest.mark.unit
def test_campaign_brief_accepts_structured_theme_discovery_brief():
    brief = _make_brief()
    theme_discovery = ThemeDiscoveryBrief(
        business_background="AI agent marketplace helping businesses validate value before paying.",
        objective="Generate YouTube-led inbound discovery calls.",
        industry="AI services",
        locality="India",
        target_audience="SMB founders and growth leaders",
        persona="Founder evaluating AI execution help",
        tone="clear and credible",
        offer="7-day free trial with keep-the-work guarantee",
        channel_intent=ThemeDiscoveryChannelIntent(
            primary_destination="youtube",
            supported_live_destinations=["youtube"],
            content_formats=["shorts", "community_posts"],
            call_to_action="Book a discovery call",
        ),
        success_metrics=[SuccessMetric(name="qualified_leads", target="10 per month")],
    )

    enriched = brief.model_copy(update={"theme_discovery": theme_discovery})

    assert enriched.theme_discovery is not None
    assert enriched.theme_discovery.channel_intent.primary_destination == "youtube"
    assert enriched.theme_discovery.success_metrics[0].name == "qualified_leads"
