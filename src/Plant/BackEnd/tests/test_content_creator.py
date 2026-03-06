"""Tests for ContentCreatorSkill (E2-S1)."""
from __future__ import annotations

from datetime import date

import pytest

from agent_mold.skills.content_creator import ContentCreatorSkill
from agent_mold.skills.content_models import (
    Campaign,
    CampaignBrief,
    DestinationRef,
    PostGeneratorInput,
    PostingSchedule,
    estimate_cost,
)
from agent_mold.skills.grok_client import GrokClientError


def _make_campaign(
    duration_days: int = 30,
    times_per_day: int = 1,
    num_destinations: int = 5,
    preferred_hours: list[int] | None = None,
) -> Campaign:
    destinations = [
        DestinationRef(destination_type=f"linkedin") if i == 0
        else DestinationRef(destination_type=f"instagram") if i == 1
        else DestinationRef(destination_type=f"youtube") if i == 2
        else DestinationRef(destination_type=f"facebook") if i == 3
        else DestinationRef(destination_type=f"simulated")
        for i in range(num_destinations)
    ]
    schedule = PostingSchedule(
        times_per_day=times_per_day,
        preferred_hours_utc=preferred_hours or [9],
    )
    brief = CampaignBrief(
        theme="Hire AI Agents — WAOOAW",
        start_date=date(2026, 3, 6),
        duration_days=duration_days,
        destinations=destinations,
        schedule=schedule,
        brand_name="WAOOAW",
        audience="SMB founders",
        tone="inspiring",
    )
    cost = estimate_cost(brief, model_used="deterministic")
    return Campaign(
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=brief,
        cost_estimate=cost,
    )


@pytest.mark.unit
def test_generate_theme_list_deterministic_30_days_5_destinations(monkeypatch):
    """E2-S1-T1: generate_theme_list deterministic, 30 days, 5 destinations → 30 theme items"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    campaign = _make_campaign(duration_days=30, num_destinations=5)
    skill = ContentCreatorSkill()
    output = skill.generate_theme_list(campaign)

    assert output.campaign_id == campaign.campaign_id
    assert len(output.theme_items) == 30


@pytest.mark.unit
def test_generate_posts_for_theme_3_destinations(monkeypatch):
    """E2-S1-T2: generate_posts_for_theme 3 destinations → 3 posts"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    campaign = _make_campaign(duration_days=7, num_destinations=3)
    skill = ContentCreatorSkill()
    theme_output = skill.generate_theme_list(campaign)
    first_theme = theme_output.theme_items[0]

    inp = PostGeneratorInput(campaign=campaign, theme_item=first_theme)
    post_output = skill.generate_posts_for_theme(inp)

    assert post_output.theme_item_id == first_theme.theme_item_id
    assert len(post_output.posts) == 3


@pytest.mark.unit
def test_post_content_text_is_non_empty(monkeypatch):
    """E2-S1-T3: Post content_text is non-empty string for all destinations"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    campaign = _make_campaign(duration_days=7, num_destinations=3)
    skill = ContentCreatorSkill()
    theme_output = skill.generate_theme_list(campaign)
    first_theme = theme_output.theme_items[0]

    inp = PostGeneratorInput(campaign=campaign, theme_item=first_theme)
    post_output = skill.generate_posts_for_theme(inp)

    for post in post_output.posts:
        assert isinstance(post.content_text, str)
        assert len(post.content_text) > 0


@pytest.mark.unit
def test_grok_backend_without_api_key_raises_grok_client_error(monkeypatch):
    """E2-S1-T4: With EXECUTOR_BACKEND=grok and no XAI_API_KEY, raises GrokClientError"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "grok")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    campaign = _make_campaign(duration_days=7, num_destinations=1)
    skill = ContentCreatorSkill()

    with pytest.raises(GrokClientError):
        skill.generate_theme_list(campaign)


@pytest.mark.unit
def test_scheduled_publish_at_hour_matches_preferred_hour(monkeypatch):
    """E2-S1-T5: scheduled_publish_at.hour matches preferred_hours_utc[0]"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    preferred_hour = 14
    campaign = _make_campaign(
        duration_days=7,
        num_destinations=2,
        preferred_hours=[preferred_hour],
    )
    skill = ContentCreatorSkill()
    theme_output = skill.generate_theme_list(campaign)
    first_theme = theme_output.theme_items[0]

    inp = PostGeneratorInput(campaign=campaign, theme_item=first_theme)
    post_output = skill.generate_posts_for_theme(inp)

    for post in post_output.posts:
        assert post.scheduled_publish_at.hour == preferred_hour
