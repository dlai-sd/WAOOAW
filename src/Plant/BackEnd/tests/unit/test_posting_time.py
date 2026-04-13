"""Unit tests for posting-time recommendations — E6-S1.

Tests that get_posting_time_suggestions returns industry-specific
recommendations with day, time, and reason.
"""
from __future__ import annotations

import pytest

from services.content_analytics import get_posting_time_suggestions


class TestPostingTimeRecommendations:
    """E6-S1: Posting-time optimization."""

    @pytest.mark.asyncio
    async def test_returns_education_posting_times(self):
        """E6-S1-T1: Returns 3 posting time recommendations for education industry."""
        suggestions = await get_posting_time_suggestions("education", "youtube")
        
        assert len(suggestions) == 3
        for suggestion in suggestions:
            assert "day" in suggestion
            assert "time" in suggestion
            assert "reason" in suggestion
        
        # Check specific education defaults
        assert suggestions[0]["day"] == "Monday"
        assert "8:00 AM" in suggestions[0]["time"]
        assert "study" in suggestions[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_fallback_for_unknown_industry(self):
        """E6-S1-T2: Returns marketing defaults for unknown industry."""
        suggestions = await get_posting_time_suggestions("unknown_industry", "youtube")
        
        assert len(suggestions) == 3
        # Should return marketing defaults
        assert suggestions[0]["day"] == "Tuesday"
        assert "10:00 AM" in suggestions[0]["time"]
        assert "B2B" in suggestions[0]["reason"]

    @pytest.mark.asyncio
    async def test_marketing_industry_posting_times(self):
        """E6-S1: Verify marketing industry returns expected recommendations."""
        suggestions = await get_posting_time_suggestions("marketing", "linkedin")
        
        assert len(suggestions) == 3
        assert suggestions[0]["day"] == "Tuesday"
        assert suggestions[1]["day"] == "Thursday"
        assert suggestions[2]["day"] == "Saturday"
