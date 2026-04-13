"""Unit tests for DMA market context injection — E5-S1, E5-S2.

Tests that competitor/niche context is captured in discovery and injected
into content generation.
"""
from __future__ import annotations

import json

import pytest

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
