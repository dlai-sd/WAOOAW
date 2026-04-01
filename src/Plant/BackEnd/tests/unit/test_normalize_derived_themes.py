from __future__ import annotations

import pytest

from api.v1.digital_marketing_activation import _normalize_derived_themes


@pytest.mark.unit
class TestNormalizeDerivedThemes:
    """Tests for _normalize_derived_themes covering AI response edge cases."""

    def test_list_of_dicts_normal_case(self):
        raw = [
            {"title": "SEO Tips", "description": "Weekly SEO advice", "frequency": "weekly"},
            {"title": "Brand Stories", "description": "Monthly brand content", "frequency": "monthly"},
        ]
        result = _normalize_derived_themes(raw)
        assert len(result) == 2
        assert result[0] == {"title": "SEO Tips", "description": "Weekly SEO advice", "frequency": "weekly"}
        assert result[1] == {"title": "Brand Stories", "description": "Monthly brand content", "frequency": "monthly"}

    def test_list_of_strings_bug_case(self):
        """AI sometimes returns plain strings instead of dicts — this was the ValueError."""
        raw = ["SEO Tips", "Brand Building", "Customer Engagement"]
        result = _normalize_derived_themes(raw)
        assert len(result) == 3
        assert result[0] == {"title": "SEO Tips", "description": "", "frequency": "weekly"}
        assert result[1] == {"title": "Brand Building", "description": "", "frequency": "weekly"}
        assert result[2] == {"title": "Customer Engagement", "description": "", "frequency": "weekly"}

    def test_mixed_strings_and_dicts(self):
        raw = [
            "Quick Tips",
            {"title": "Deep Dives", "description": "Long-form analysis", "frequency": "monthly"},
        ]
        result = _normalize_derived_themes(raw)
        assert len(result) == 2
        assert result[0] == {"title": "Quick Tips", "description": "", "frequency": "weekly"}
        assert result[1] == {"title": "Deep Dives", "description": "Long-form analysis", "frequency": "monthly"}

    def test_empty_list(self):
        assert _normalize_derived_themes([]) == []

    def test_not_a_list_returns_empty(self):
        assert _normalize_derived_themes(None) == []
        assert _normalize_derived_themes("some string") == []
        assert _normalize_derived_themes(42) == []
        assert _normalize_derived_themes({"title": "solo"}) == []

    def test_empty_strings_skipped(self):
        raw = ["", "  ", "Valid Theme"]
        result = _normalize_derived_themes(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Valid Theme"

    def test_dicts_without_title_skipped(self):
        raw = [
            {"description": "No title here"},
            {"title": "", "description": "Empty title"},
            {"title": "  ", "description": "Whitespace title"},
            {"title": "Real Theme", "description": "Has title"},
        ]
        result = _normalize_derived_themes(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Real Theme"

    def test_frequency_defaults_to_weekly(self):
        raw = [{"title": "No Freq"}]
        result = _normalize_derived_themes(raw)
        assert result[0]["frequency"] == "weekly"

    def test_non_dict_non_string_items_skipped(self):
        raw = [42, None, True, ["nested"], {"title": "Valid"}]
        result = _normalize_derived_themes(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Valid"

    def test_whitespace_stripped(self):
        raw = [{"title": "  Padded Title  ", "description": "  Padded Desc  ", "frequency": "  daily  "}]
        result = _normalize_derived_themes(raw)
        assert result[0] == {"title": "Padded Title", "description": "Padded Desc", "frequency": "daily"}
