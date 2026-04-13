"""Tests for DMA auto-draft generation including artifact rendering."""

import pytest

from api.v1.digital_marketing_activation import _build_auto_draft
from services.draft_batches import DraftPostRecord


class TestE3S1TableArtifactRendering:
    """E3-S1: Fix table artifact rendering with structured preview and markdown fallback"""

    @pytest.mark.asyncio
    async def test_build_auto_draft_table_has_structured_preview(self):
        """E3-S1-T1: Call _build_auto_draft with 3 derived themes and TABLE artifact type"""
        from datetime import datetime, timezone
        from api.v1 import hired_agents_simple
        from agent_mold.skills.playbook import ArtifactType
        
        now = datetime.now(timezone.utc)
        # Mock hired agent record with all required fields
        record = hired_agents_simple._HiredAgentRecord(
            hired_instance_id="hired-123",
            subscription_id="sub-123",
            agent_id="agent-123",
            agent_type_id="marketing.digital_marketing.v1",
            customer_id="cust-123",
            nickname="Test DMA",
            theme=None,
            config={},
            configured=True,
            goals_completed=False,
            active=True,
            trial_status="active",
            trial_start_at=now,
            trial_end_at=now,
            created_at=now,
            updated_at=now,
        )
        
        workspace = {
            "brand_name": "Test Brand",
            "location": "Mumbai",
            "primary_language": "en",
            "campaign_setup": {
                "master_theme": "Master Theme Test",
                "derived_themes": [
                    {"title": "Theme 1", "description": "Description 1", "frequency": "weekly"},
                    {"title": "Theme 2", "description": "Description 2", "frequency": "biweekly"},
                    {"title": "Theme 3", "description": "Description 3", "frequency": "monthly"},
                ],
            },
        }
        
        batch = await _build_auto_draft(
            record=record,
            workspace=workspace,
            master_theme="Master Theme Test",
            campaign_id=None,
            artifact_types=[ArtifactType.TABLE],
            db=None,
        )
        
        # Should have one post with table artifact
        assert "posts" in batch
        assert len(batch["posts"]) == 1
        
        post = batch["posts"][0]
        assert post["artifact_type"] == "table"
        assert "artifact_metadata" in post
        assert "table_preview" in post["artifact_metadata"]
        
        table_preview = post["artifact_metadata"]["table_preview"]
        assert "columns" in table_preview
        assert "rows" in table_preview
        assert len(table_preview["columns"]) == 4
        assert table_preview["columns"] == ["#", "Theme", "Description", "Frequency"]
        assert len(table_preview["rows"]) == 3
        
        # Check first row content
        row1 = table_preview["rows"][0]
        assert row1["#"] == "1"
        assert row1["Theme"] == "Theme 1"
        assert row1["Description"] == "Description 1"
        assert row1["Frequency"] == "weekly"
