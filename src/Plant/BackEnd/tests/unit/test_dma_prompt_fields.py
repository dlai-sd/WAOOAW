"""Tests for DMA prompt field requirements, progress tracking, and validation gates."""

import json
from typing import Any

import pytest

from agent_mold.reference_agents import THEME_DISCOVERY_REQUIRED_FIELDS
from api.v1.digital_marketing_activation import (
    _normalize_workshop_messages,
    _parse_theme_workshop_response,
    _theme_workshop_prompt,
)


class TestE1S1PromptRewrite:
    """E1-S1: Rewrite system prompt with required-fields checklist"""

    def test_required_fields_checklist_with_6_filled(self):
        """E1-S1-T1: Call _theme_workshop_prompt with 6 of 11 summary fields filled"""
        workspace = {
            "brand_name": "Test Brand",
            "location": "Mumbai",
            "primary_language": "en",
            "timezone": "Asia/Kolkata",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {
                    "business_focus": "Fitness coaching",  # business_background
                    "business_goal": "Generate leads",  # objective
                    "profession_name": "Fitness",  # industry
                    "location_focus": "Mumbai",  # locality
                    "audience": "Working professionals",  # target_audience
                    "customer_profile": "30-45 years",  # persona
                    # tone, cta, youtube_angle, first_content_direction, positioning are missing
                },
                "follow_up_questions": [],
            },
            "schedule": {},
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup)
        prompt = json.loads(prompt_json)

        checklist = prompt["workshop_state"]["required_fields_checklist"]
        assert checklist["filled"] == 6
        assert checklist["total"] == 11
        assert checklist["missing"] == 5
        assert len(checklist["locked_fields"]) == 6
        assert len(checklist["missing_fields"]) == 5

    def test_normalize_workshop_messages_returns_12_messages(self):
        """E1-S1-T2: Call _normalize_workshop_messages with 15 messages"""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(15)
        ]
        normalized = _normalize_workshop_messages(messages)
        assert len(normalized) == 12  # not 4

    def test_all_fields_filled_missing_fields_empty(self):
        """E1-S1-T3: Call _theme_workshop_prompt with all 11 fields filled"""
        workspace = {
            "brand_name": "Test Brand",
            "location": "Mumbai",
            "primary_language": "en",
            "timezone": "Asia/Kolkata",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {
                    "business_focus": "Fitness coaching",
                    "business_goal": "Generate leads",
                    "profession_name": "Fitness",
                    "location_focus": "Mumbai",
                    "audience": "Working professionals",
                    "customer_profile": "30-45 years",
                    "tone": "Motivational",
                    "cta": "Book a free consultation",
                    "youtube_angle": "Quick workout tips",
                    "first_content_direction": "Weekly workout series",
                    "positioning": "Premium local fitness coach",
                },
                "follow_up_questions": [],
            },
            "schedule": {},
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup)
        prompt = json.loads(prompt_json)

        checklist = prompt["workshop_state"]["required_fields_checklist"]
        assert checklist["filled"] == 11
        assert checklist["missing"] == 0
        assert len(checklist["missing_fields"]) == 0

    def test_system_prompt_contains_produce_immediately_rule(self):
        """E1-S1-T4: Extract system prompt text and verify O6 enforcement"""
        # This test verifies the system prompt will contain the deliverable rule
        # The actual system prompt is passed to grok_complete in generate_theme_plan
        # We can verify it indirectly by checking the code contains the expected text
        from api.v1.digital_marketing_activation import generate_theme_plan
        import inspect
        
        source = inspect.getsource(generate_theme_plan)
        # The system prompt must contain the exact O6 enforcement phrase
        assert "produce it immediately" in source.lower()


class TestE1S2FieldCompletenessValidation:
    """E1-S2: Server-side field-completeness validation before approval_ready transition"""

    def test_llm_approval_with_insufficient_fields_forced_to_discovery(self):
        """E1-S2-T1: LLM says approval_ready but only 5 fields filled → status forced to discovery"""
        raw_response = json.dumps({
            "assistant_message": "Great! Here's your strategy.",
            "status": "approval_ready",
            "master_theme": "Test Master Theme",
            "derived_themes": [
                {"title": "Theme 1", "description": "Test", "frequency": "weekly"}
            ],
            "summary": {
                "business_focus": "Fitness coaching",
                "business_goal": "Generate leads",
                "profession_name": "Fitness",
                "location_focus": "Mumbai",
                "audience": "Working professionals",
                # Only 5 fields filled, missing 6 more
            },
            "checkpoint_summary": "Strategy is ready",
            "current_focus_question": "",
            "next_step_options": ["Approve"],
        })
        
        workspace = {"brand_name": "Test"}
        existing_workshop = {"messages": [], "summary": {}}
        
        master_theme, derived_themes, workshop = _parse_theme_workshop_response(
            raw_response,
            workspace=workspace,
            existing_workshop=existing_workshop,
            pending_input="",
        )
        
        # Should be forced to discovery because only 5 < 9 fields filled
        assert workshop["status"] == "discovery"

    def test_llm_approval_with_all_fields_passes_through(self):
        """E1-S2-T2: LLM says approval_ready and all 11 fields filled → status stays approval_ready"""
        raw_response = json.dumps({
            "assistant_message": "Great! Here's your strategy.",
            "status": "approval_ready",
            "master_theme": "Test Master Theme",
            "derived_themes": [
                {"title": "Theme 1", "description": "Test", "frequency": "weekly"}
            ],
            "summary": {
                "business_focus": "Fitness coaching",
                "business_goal": "Generate leads",
                "profession_name": "Fitness",
                "location_focus": "Mumbai",
                "audience": "Working professionals",
                "customer_profile": "30-45 years",
                "tone": "Motivational",
                "cta": "Book consultation",
                "youtube_angle": "Quick tips",
                "first_content_direction": "Weekly series",
                "positioning": "Premium coach",
            },
            "checkpoint_summary": "Strategy is ready",
            "current_focus_question": "",
            "next_step_options": ["Approve"],
        })
        
        workspace = {"brand_name": "Test"}
        existing_workshop = {"messages": [], "summary": {}}
        
        master_theme, derived_themes, workshop = _parse_theme_workshop_response(
            raw_response,
            workspace=workspace,
            existing_workshop=existing_workshop,
            pending_input="",
        )
        
        # All 11 fields filled, should stay approval_ready
        assert workshop["status"] == "approval_ready"


class TestE2S1FieldProgressCounter:
    """E2-S1: Add field-level progress counter to response contract and wizard UI"""

    def test_brief_progress_with_7_filled_fields(self):
        """E2-S1-T1: Parse a workshop response with 7 filled summary fields"""
        raw_response = json.dumps({
            "assistant_message": "We're making good progress.",
            "status": "discovery",
            "summary": {
                "business_focus": "Fitness coaching",
                "business_goal": "Generate leads",
                "profession_name": "Fitness",
                "location_focus": "Mumbai",
                "audience": "Working professionals",
                "customer_profile": "30-45 years",
                "tone": "Motivational",
                # Missing: cta, youtube_angle, first_content_direction, positioning
            },
            "checkpoint_summary": "Getting closer",
            "current_focus_question": "What action should viewers take?",
            "next_step_options": ["Continue"],
        })
        
        workspace = {"brand_name": "Test"}
        existing_workshop = {"messages": [], "summary": {}}
        
        master_theme, derived_themes, workshop = _parse_theme_workshop_response(
            raw_response,
            workspace=workspace,
            existing_workshop=existing_workshop,
            pending_input="",
        )
        
        assert "brief_progress" in workshop
        assert workshop["brief_progress"]["filled"] == 7
        assert workshop["brief_progress"]["total"] == 11
        assert len(workshop["brief_progress"]["missing_fields"]) == 4
        assert len(workshop["brief_progress"]["locked_fields"]) == 7


class TestE2S2FieldNameAlignment:
    """E2-S2: Align workshop summary field names to required-fields list"""

    def test_response_contract_summary_maps_to_all_required_fields(self):
        """E2-S2-T1: Call _theme_workshop_prompt and verify summary field mappings"""
        workspace = {
            "brand_name": "Test Brand",
            "location": "Mumbai",
            "primary_language": "en",
            "timezone": "Asia/Kolkata",
        }
        campaign_setup = {
            "strategy_workshop": {
                "status": "discovery",
                "messages": [],
                "summary": {},
                "follow_up_questions": [],
            },
            "schedule": {},
        }

        prompt_json = _theme_workshop_prompt(workspace, campaign_setup)
        prompt = json.loads(prompt_json)

        # Verify the response_contract.summary has all expected field mappings
        summary_spec = prompt["response_contract"]["summary"]
        
        # Check that each of the 11 required fields has a corresponding summary key
        # via the _FIELD_TO_SUMMARY_KEY mapping
        _FIELD_TO_SUMMARY_KEY = {
            "business_background": "business_focus",
            "objective": "business_goal",
            "industry": "profession_name",
            "locality": "location_focus",
            "target_audience": "audience",
            "persona": "customer_profile",
            "tone": "tone",
            "offer": "cta",
            "channel_intent": "youtube_angle",
            "posting_cadence": "first_content_direction",
            "success_metrics": "positioning",
        }
        
        # All mapped summary keys should exist in the response contract
        for req_field, summary_key in _FIELD_TO_SUMMARY_KEY.items():
            assert summary_key in summary_spec, f"Missing summary key {summary_key} for required field {req_field}"
