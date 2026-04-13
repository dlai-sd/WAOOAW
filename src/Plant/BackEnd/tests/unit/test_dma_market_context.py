"""Unit tests for DMA market context injection — E5-S1, E5-S2.

Tests that competitor/niche context is captured in discovery and injected
into content generation.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agent_mold.skills.content_creator import ContentCreatorProcessor
from agent_mold.skills.content_models import (
    Campaign,
    CampaignBrief,
    CostEstimate,
    DailyThemeItem,
    DestinationRef,
    PostGeneratorInput,
    PostingSchedule,
)
from api.v1.digital_marketing_activation import _theme_workshop_prompt


class TestCompetitorNicheDiscovery:
    """E5-S1: Competitor/niche context fields in discovery."""

    def test_system_prompt_mentions_competitor(self):
        """E5-S1-T1: System prompt contains competitor discovery instruction."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": ["service1"],
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
            }
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup)
        prompt_data = json.loads(prompt_json)

        # Check response contract summary includes the new fields
        assert "response_contract" in prompt_data
        assert "summary" in prompt_data["response_contract"]
        summary_contract = prompt_data["response_contract"]["summary"]
        assert "competitor_names" in summary_contract
        assert "niche_keywords" in summary_contract

    def test_response_contract_has_competitor_niche_fields(self):
        """E5-S1-T2: Response contract summary section contains competitor_names and niche_keywords keys."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": ["service1"],
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
            }
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup)
        prompt_data = json.loads(prompt_json)

        summary_contract = prompt_data["response_contract"]["summary"]
        # Verify both fields exist in the response contract
        assert isinstance(summary_contract.get("competitor_names"), list)
        assert isinstance(summary_contract.get("niche_keywords"), list)


class TestNicheHashtagInjection:
    """E5-S2: Niche hashtags and SEO keywords in content generation."""

    @patch("agent_mold.skills.content_creator.grok_complete")
    @patch("agent_mold.skills.content_creator.get_grok_client")
    def test_grok_posts_includes_niche_keywords(self, mock_get_client, mock_grok_complete):
        """E5-S2-T1: The prompt sent to Grok contains niche keywords."""
        mock_get_client.return_value = MagicMock()
        mock_grok_complete.return_value = "Test post content #aiTutoring #edtech"

        brief = CampaignBrief(
            theme="AI Tutoring Excellence",
            brand_name="EduTech Pro",
            audience="Parents of school students",
            tone="Educational",
            language="en",
            start_date=date(2026, 4, 15),
            duration_days=7,
            destinations=[DestinationRef(destination_type="youtube", handle="@edutech")],
            schedule=PostingSchedule(times_per_day=1, preferred_hours_utc=[9]),
        )
        campaign = Campaign(
            hired_instance_id="test-hired-1",
            customer_id="test-cust-1",
            brief=brief,
            cost_estimate=CostEstimate(
                total_theme_items=7,
                total_posts=7,
                llm_calls=8,
                cost_per_call_usd=0.0,
                total_cost_usd=0.0,
                total_cost_inr=0.0,
                model_used="grok-3-latest",
            ),
        )
        theme_item = DailyThemeItem(
            campaign_id=campaign.campaign_id,
            day_number=1,
            scheduled_date=date(2026, 4, 15),
            theme_title="AI Tutoring Tips",
            theme_description="Best practices for online learning",
            dimensions=["education", "technology"],
        )
        inp = PostGeneratorInput(
            campaign=campaign,
            theme_item=theme_item,
            niche_keywords=["ai tutoring", "edtech"],
            competitor_context=["Khan Academy"],
        )

        processor = ContentCreatorProcessor()
        posts = processor._grok_posts(inp)

        # Verify grok_complete was called with niche keywords in the prompt
        assert mock_grok_complete.called
        call_args = mock_grok_complete.call_args
        user_prompt = call_args[0][2]  # third positional arg is user prompt
        assert "ai tutoring" in user_prompt.lower()
        assert "edtech" in user_prompt.lower()

    @patch("agent_mold.skills.content_creator.grok_complete")
    @patch("agent_mold.skills.content_creator.get_grok_client")
    def test_grok_posts_graceful_without_niche_keywords(self, mock_get_client, mock_grok_complete):
        """E5-S2-T2: Prompt does not break when niche_keywords is empty."""
        mock_get_client.return_value = MagicMock()
        mock_grok_complete.return_value = "Test post content"

        brief = CampaignBrief(
            theme="General Content",
            brand_name="Test Brand",
            audience="General audience",
            tone="Friendly",
            language="en",
            start_date=date(2026, 4, 15),
            duration_days=7,
            destinations=[DestinationRef(destination_type="linkedin", handle="@testbrand")],
            schedule=PostingSchedule(times_per_day=1, preferred_hours_utc=[9]),
        )
        campaign = Campaign(
            hired_instance_id="test-hired-2",
            customer_id="test-cust-2",
            brief=brief,
            cost_estimate=CostEstimate(
                total_theme_items=7,
                total_posts=7,
                llm_calls=8,
                cost_per_call_usd=0.0,
                total_cost_usd=0.0,
                total_cost_inr=0.0,
                model_used="deterministic",
            ),
        )
        theme_item = DailyThemeItem(
            campaign_id=campaign.campaign_id,
            day_number=1,
            scheduled_date=date(2026, 4, 15),
            theme_title="Generic Theme",
            theme_description="Generic description",
            dimensions=[],
        )
        inp = PostGeneratorInput(
            campaign=campaign,
            theme_item=theme_item,
            niche_keywords=[],
            competitor_context=[],
        )

        processor = ContentCreatorProcessor()
        posts = processor._grok_posts(inp)

        # Verify it doesn't crash and produces posts
        assert len(posts) == 1
        assert posts[0].content_text == "Test post content"

