"""End-to-end integration test for DMA conversation → content pipeline.

Tests the complete DMA workflow from initial conversation through content
generation, artifact creation, and publishing readiness.

DMA-CONV-1 E9-S1
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.reference_agents import THEME_DISCOVERY_REQUIRED_FIELDS


class TestDMAEndToEnd:
    """Full-path DMA conversation → theme → content → artifact validation."""

    @pytest.fixture
    def mock_hired_agent(self):
        """Mock hired agent instance for testing."""
        return {
            "hired_instance_id": str(uuid4()),
            "customer_id": "test-customer-123",
            "agent_id": "dma-v1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Test DMA",
            "theme": "Digital Marketing",
            "config": {
                "digital_marketing_activation": {
                    "brand_name": "Test Business",
                    "location": "Test City",
                    "business_context": "A test business",
                    "offerings_services": ["service1", "service2"],
                }
            },
            "configured": True,
            "updated_at": "2026-04-13T00:00:00Z",
        }

    @pytest.fixture
    def mock_workshop_full_fields(self):
        """Mock workshop summary with all 11 required fields filled."""
        return {
            "business_focus": "Premium beauty services",
            "business_goal": "Get 20 new bookings per month",
            "profession_name": "Beauty Artist",
            "location_focus": "Mumbai suburbs",
            "audience": "Women 25-45 planning weddings or events",
            "customer_profile": "Middle-income brides and working professionals",
            "tone": "Warm, trustworthy, aspirational",
            "cta": "Book your slot today",
            "youtube_angle": "Behind-the-scenes transformation videos",
            "first_content_direction": "Bridal makeup tutorials and before-after reveals",
            "positioning": "Premium quality at affordable prices",
        }

    @pytest.fixture
    def mock_grok_approval_ready_response(self, mock_workshop_full_fields):
        """Mock Grok response when all fields are filled → approval_ready."""
        return json.dumps({
            "assistant_message": "Your strategy is ready for approval.",
            "checkpoint_summary": "We've defined your complete content strategy for bridal beauty content.",
            "current_focus_question": "",
            "next_step_options": ["Approve this strategy", "Make a final adjustment"],
            "time_saving_note": "All 11 fields are locked — you can approve now.",
            "status": "approval_ready",
            "summary": mock_workshop_full_fields,
            "master_theme": "Bridal beauty transformation stories that build trust and drive bookings",
            "derived_themes": [
                {
                    "title": "Bridal makeup tutorials",
                    "description": "Step-by-step videos showing makeup transformations",
                    "frequency": "weekly",
                    "pillar": "Educational",
                },
                {
                    "title": "Before-after reveals",
                    "description": "Showcasing real client transformations",
                    "frequency": "bi-weekly",
                    "pillar": "Customer stories",
                },
                {
                    "title": "Behind-the-scenes prep",
                    "description": "Day-of wedding prep and setup",
                    "frequency": "monthly",
                    "pillar": "Behind the scenes",
                },
            ],
        })

    @pytest.mark.asyncio
    async def test_conversation_reaches_approval_ready(
        self,
        mock_hired_agent,
        mock_workshop_full_fields,
        mock_grok_approval_ready_response,
    ):
        """E9-S1-T1: After filling all 11 required fields, status transitions to approval_ready."""
        # This test validates the full conversation flow that fills all fields
        # and transitions to approval_ready status with brief_progress.filled == 11.
        
        from api.v1.digital_marketing_activation import _parse_theme_workshop_response
        
        workspace = {
            "brand_name": "Test Business",
            "business_context": "A test business",
        }
        existing_workshop = {
            "status": "discovery",
            "messages": [],
            "summary": {},
        }
        
        _, _, workshop = _parse_theme_workshop_response(
            mock_grok_approval_ready_response,
            workspace=workspace,
            existing_workshop=existing_workshop,
            pending_input="I'm ready to approve",
        )
        
        assert workshop["status"] == "approval_ready"
        assert workshop["brief_progress"]["filled"] == 11
        assert workshop["brief_progress"]["total"] == len(THEME_DISCOVERY_REQUIRED_FIELDS)
        assert len(workshop["brief_progress"]["missing_fields"]) == 0
        assert workshop["brief_progress"]["filled"] == workshop["brief_progress"]["total"]

    @pytest.mark.asyncio
    async def test_artifact_metadata_populated_for_table(self):
        """E9-S1-T2: Table artifacts include artifact_metadata.table_preview with columns and rows."""
        from api.v1.digital_marketing_activation import _build_auto_draft
        from services.draft_batches import DatabaseDraftBatchStore
        
        # Mock the dependencies
        mock_record = MagicMock()
        mock_record.hired_instance_id = str(uuid4())
        mock_record.customer_id = "test-customer"
        
        workspace = {
            "brand_name": "Test Business",
        }
        
        derived_themes = [
            {"title": "Theme 1", "description": "Description 1", "frequency": "weekly"},
            {"title": "Theme 2", "description": "Description 2", "frequency": "bi-weekly"},
            {"title": "Theme 3", "description": "Description 3", "frequency": "monthly"},
        ]
        
        with patch("api.v1.digital_marketing_activation.DatabaseDraftBatchStore") as mock_store_class:
            mock_store = AsyncMock()
            mock_store_class.return_value = mock_store
            mock_store.save_batch.return_value = None
            
            with patch("api.v1.digital_marketing_activation._get_read_hired_agents_db_session", return_value=None):
                result = await _build_auto_draft(
                    record=mock_record,
                    workspace=workspace,
                    master_theme="Test master theme",
                    campaign_id="test-campaign-id",
                    artifact_types=[],  # Will default to TABLE
                    db=None,
                )
        
        # The result should have a batch with a table artifact post
        assert "batch_id" in result
        assert "posts" in result
        
        # Find the table post
        table_posts = [p for p in result["posts"] if p.get("artifact_type") == "table"]
        assert len(table_posts) > 0
        
        table_post = table_posts[0]
        assert "artifact_metadata" in table_post
        assert "table_preview" in table_post["artifact_metadata"]
        
        table_preview = table_post["artifact_metadata"]["table_preview"]
        assert "columns" in table_preview
        assert "rows" in table_preview
        assert len(table_preview["columns"]) == 4  # #, Theme, Description, Frequency
        assert len(table_preview["rows"]) == len(derived_themes)

    @pytest.mark.asyncio
    async def test_brand_voice_injected_when_available(self, mock_hired_agent):
        """E9-S1-T3: When customer has a brand voice, it appears in the prompt payload."""
        from api.v1.digital_marketing_activation import _theme_workshop_prompt
        
        workspace = {
            "brand_name": "Test Business",
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
            }
        }
        brand_voice_section = {
            "tone_keywords": ["bold", "direct"],
            "vocabulary_preferences": ["concise", "clear"],
            "messaging_patterns": ["action-oriented"],
            "example_phrases": ["Get started today"],
            "voice_description": "Bold and action-oriented",
        }
        
        prompt_json = _theme_workshop_prompt(
            workspace=workspace,
            campaign_setup=campaign_setup,
            brand_voice_section=brand_voice_section,
            performance_insights=None,
        )
        prompt = json.loads(prompt_json)
        
        assert "brand_voice_context" in prompt
        assert prompt["brand_voice_context"]["tone_keywords"] == ["bold", "direct"]
        assert prompt["brand_voice_context"]["voice_description"] == "Bold and action-oriented"

    @pytest.mark.asyncio
    async def test_full_conversation_to_content_flow_integration(
        self,
        mock_hired_agent,
        mock_workshop_full_fields,
        mock_grok_approval_ready_response,
    ):
        """Integration test: Full flow from conversation start to content generation."""
        from api.v1.digital_marketing_activation import _theme_workshop_prompt, _parse_theme_workshop_response
        
        # Step 1: Start with empty workshop
        workspace = {
            "brand_name": "Test Beauty Studio",
            "location": "Mumbai",
            "business_context": "Premium bridal makeup services",
            "offerings_services": ["Bridal makeup", "Event makeup"],
        }
        
        initial_workshop = {
            "status": "discovery",
            "messages": [],
            "summary": {},
        }
        
        # Step 2: Generate prompt with brand voice
        brand_voice = {
            "tone_keywords": ["warm", "trustworthy"],
            "voice_description": "Warm and aspirational",
        }
        
        prompt_json = _theme_workshop_prompt(
            workspace=workspace,
            campaign_setup={"strategy_workshop": initial_workshop},
            brand_voice_section=brand_voice,
            performance_insights=None,
        )
        prompt = json.loads(prompt_json)
        
        # Verify prompt includes brand voice and field tracking
        assert "brand_voice_context" in prompt
        assert "required_fields_checklist" in prompt["workshop_state"]
        assert prompt["workshop_state"]["required_fields_checklist"]["total"] == 11
        assert prompt["workshop_state"]["required_fields_checklist"]["filled"] == 0
        
        # Step 3: Simulate conversation completion (all fields filled)
        _, _, final_workshop = _parse_theme_workshop_response(
            mock_grok_approval_ready_response,
            workspace=workspace,
            existing_workshop=initial_workshop,
            pending_input="I'm ready to approve",
        )
        
        # Verify final state
        assert final_workshop["status"] == "approval_ready"
        assert final_workshop["brief_progress"]["filled"] == 11
        assert len(final_workshop["brief_progress"]["missing_fields"]) == 0
        assert "master_theme" in final_workshop
        assert len(final_workshop.get("derived_themes", [])) >= 3
        
        # Verify all required fields are present
        for field in THEME_DISCOVERY_REQUIRED_FIELDS:
            assert field in final_workshop["brief_progress"]["locked_fields"]
