"""Unit tests for DMA brand voice injection — E4-S1, E4-S2.

Tests that brand voice is loaded and injected into the DMA conversation prompt
and content generation pipeline.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.v1.digital_marketing_activation import _theme_workshop_prompt
from models.brand_voice import BrandVoiceModel


class TestBrandVoiceInjection:
    """E4-S1: Brand voice injection into conversation prompt."""

    def test_prompt_includes_brand_voice_when_provided(self):
        """E4-S1-T1: Prompt payload contains brand_voice_context with all fields."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": ["service1"],
            "location": "Mumbai",
            "primary_language": "en",
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
        brand_voice_section = {
            "tone_keywords": ["bold", "direct"],
            "vocabulary_preferences": ["innovate", "transform"],
            "messaging_patterns": ["problem-solution"],
            "example_phrases": ["We help you grow"],
            "voice_description": "Bold and direct",
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup, brand_voice_section)

        import json
        prompt_data = json.loads(prompt_json)
        assert "brand_voice_context" in prompt_data
        assert prompt_data["brand_voice_context"]["tone_keywords"] == ["bold", "direct"]
        assert prompt_data["brand_voice_context"]["vocabulary_preferences"] == ["innovate", "transform"]
        assert prompt_data["brand_voice_context"]["messaging_patterns"] == ["problem-solution"]
        assert prompt_data["brand_voice_context"]["example_phrases"] == ["We help you grow"]
        assert prompt_data["brand_voice_context"]["voice_description"] == "Bold and direct"

    def test_prompt_graceful_when_no_brand_voice(self):
        """E4-S1-T2: Prompt payload contains empty brand_voice_context when no brand voice."""
        workspace = {
            "brand_name": "Test Brand",
            "offerings_services": ["service1"],
            "location": "Mumbai",
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

        # No brand voice section provided
        prompt_json = _theme_workshop_prompt(workspace, campaign_setup, brand_voice_section=None)

        import json
        prompt_data = json.loads(prompt_json)
        assert "brand_voice_context" in prompt_data
        assert prompt_data["brand_voice_context"] == {}


class TestContentPillarFramework:
    """E4-S2: Content pillar framework in prompt."""

    def test_system_prompt_includes_content_pillar_guidance(self):
        """E4-S2-T1: System prompt contains content pillar guidance."""
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

        import json
        prompt_data = json.loads(prompt_json)
        
        # Check that response contract includes content_pillars field
        assert "response_contract" in prompt_data
        assert "summary" in prompt_data["response_contract"]
        assert "content_pillars" in prompt_data["response_contract"]["summary"]
