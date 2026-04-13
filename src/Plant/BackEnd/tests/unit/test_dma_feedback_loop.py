"""Unit tests for DMA performance feedback loop integration.

Tests that performance analytics are correctly injected into the DMA
conversation prompt to enable autonomous improvement over time.

DMA-CONV-1 E7-S1
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

from api.v1.digital_marketing_activation import _theme_workshop_prompt
from services.content_analytics import ContentRecommendation


class TestDMAFeedbackLoop:
    """Performance analytics injection into DMA prompt."""

    def test_performance_insights_with_data(self):
        """When performance data exists, prompt includes insights."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": ["service1"],
            "location": "Test Location",
            "primary_language": "en",
            "timezone": "UTC",
            "business_context": "test context",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
                "pending_input": "",
            }
        }
        performance_insights = {
            "top_performing_dimensions": ["video", "carousel"],
            "best_posting_hours": [9, 14, 18],
            "avg_engagement_rate": 4.2,
            "recommendation_summary": "Focus on video and carousel content",
        }

        prompt_json = _theme_workshop_prompt(
            workspace=workspace,
            campaign_setup=campaign_setup,
            brand_voice_section=None,
            performance_insights=performance_insights,
        )
        prompt = json.loads(prompt_json)

        assert "performance_insights" in prompt
        assert prompt["performance_insights"]["avg_engagement_rate"] == 4.2
        assert "video" in prompt["performance_insights"]["top_performing_dimensions"]
        assert prompt["performance_insights"]["best_posting_hours"] == [9, 14, 18]
        assert "video and carousel" in prompt["performance_insights"]["recommendation_summary"]

    def test_performance_insights_empty_when_no_data(self):
        """When no performance data, insights section is empty dict."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": [],
            "location": "",
            "primary_language": "en",
            "timezone": "UTC",
            "business_context": "",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
            }
        }

        prompt_json = _theme_workshop_prompt(
            workspace=workspace,
            campaign_setup=campaign_setup,
            brand_voice_section=None,
            performance_insights={},
        )
        prompt = json.loads(prompt_json)

        assert "performance_insights" in prompt
        assert prompt["performance_insights"] == {}

    def test_performance_insights_graceful_when_none(self):
        """When performance_insights is None, defaults to empty dict."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": [],
            "location": "",
            "primary_language": "en",
            "timezone": "UTC",
            "business_context": "",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
            }
        }

        prompt_json = _theme_workshop_prompt(
            workspace=workspace,
            campaign_setup=campaign_setup,
            brand_voice_section=None,
            performance_insights=None,
        )
        prompt = json.loads(prompt_json)

        assert "performance_insights" in prompt
        assert prompt["performance_insights"] == {}
