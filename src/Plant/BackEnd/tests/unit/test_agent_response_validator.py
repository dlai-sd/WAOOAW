"""Tests for Agent Response Contract + Validator.

Simulates WAOOAW customer scenarios where the DMA agent's LLM responses must be
validated before reaching the customer on the CP portal.
"""

import json

import pytest

from services.agent_response_validator import (
    ResponseValidationError,
    detect_filler,
    validate_theme_plan_response,
    validate_workshop_response,
)


# ---------------------------------------------------------------------------
# Filler detection
# ---------------------------------------------------------------------------

class TestDetectFiller:
    """Filler detection catches conversational fluff common in LLM responses."""

    @pytest.mark.parametrize("text,expected", [
        ("I'm thrilled to present your content calendar!", True),
        ("I'm excited to help you today!", True),
        ("Certainly! Here is your plan...", True),
        ("Of course! Let me show you", True),
        ("Absolutely! Great question.", True),
        ("Thank you for sharing your business details", True),
        ("I'd love to help you with that", True),
        ("What a wonderful business idea!", True),
        # Non-filler: actual structured or actionable content
        ("Yoga Morning Routines", False),
        ('{"master_theme": "Bridal Beauty"}', False),
        ("Your content calendar has 4 themes focused on...", False),
        ("The analysis shows engagement peaks at 9am", False),
        ("Approve this direction to proceed", False),
        ("", False),
    ])
    def test_filler_detection(self, text: str, expected: bool) -> None:
        assert detect_filler(text) is expected


# ---------------------------------------------------------------------------
# Theme plan response validation
# ---------------------------------------------------------------------------

class TestValidateThemePlanResponse:
    """Customer scenario: DMA agent returns theme plans from the LLM."""

    def test_valid_json_theme_plan(self) -> None:
        """Agent returns well-formed JSON — validation passes."""
        response = json.dumps({
            "master_theme": "Bridal Beauty Transformations",
            "derived_themes": [
                {"title": "Bridal Tutorials", "description": "Step-by-step looks", "frequency": "weekly"},
                {"title": "Skincare Prep", "description": "Pre-wedding skincare", "frequency": "weekly"},
            ],
        })
        contract = validate_theme_plan_response(response)
        assert contract.master_theme == "Bridal Beauty Transformations"
        assert len(contract.derived_themes) == 2
        assert contract.derived_themes[0].title == "Bridal Tutorials"

    def test_plain_text_master_theme(self) -> None:
        """Agent returns plain text — first line used as master theme."""
        contract = validate_theme_plan_response("Yoga Studio Growth Strategy")
        assert contract.master_theme == "Yoga Studio Growth Strategy"
        assert len(contract.derived_themes) == 0

    def test_empty_response_raises(self) -> None:
        """Empty LLM response must raise, not pass through silently."""
        with pytest.raises(ResponseValidationError) as exc_info:
            validate_theme_plan_response("")
        assert any(v.rule == "non_empty" for v in exc_info.value.violations)

    def test_filler_response_raises(self) -> None:
        """Conversational filler must be caught, not passed to customer."""
        with pytest.raises(ResponseValidationError) as exc_info:
            validate_theme_plan_response(
                "I'm thrilled to present your amazing content calendar! Here's what I've created for you..."
            )
        assert any(v.rule == "no_filler" for v in exc_info.value.violations)

    def test_json_with_filler_master_theme_raises(self) -> None:
        """JSON response where master_theme itself is filler."""
        response = json.dumps({
            "master_theme": "I'm excited to help you with your bridal beauty business!",
            "derived_themes": [],
        })
        with pytest.raises(ResponseValidationError):
            validate_theme_plan_response(response)

    def test_require_themes_flag(self) -> None:
        """When require_themes=True, empty derived_themes must fail."""
        response = json.dumps({
            "master_theme": "Yoga Studio Growth",
            "derived_themes": [],
        })
        with pytest.raises(ResponseValidationError) as exc_info:
            validate_theme_plan_response(response, require_themes=True)
        assert any(v.rule == "non_empty_when_required" for v in exc_info.value.violations)

    def test_require_themes_passes_with_themes(self) -> None:
        """When require_themes=True and themes exist, validation passes."""
        response = json.dumps({
            "master_theme": "Yoga Studio Growth",
            "derived_themes": [
                {"title": "Morning Routines", "description": "Sunrise yoga", "frequency": "daily"},
            ],
        })
        contract = validate_theme_plan_response(response, require_themes=True)
        assert len(contract.derived_themes) == 1

    def test_non_object_json_raises(self) -> None:
        """JSON array instead of object must be caught."""
        with pytest.raises(ResponseValidationError) as exc_info:
            validate_theme_plan_response("[1, 2, 3]")
        assert any(v.rule == "must_be_object" for v in exc_info.value.violations)

    def test_theme_field_aliases(self) -> None:
        """Agent may return 'theme' instead of 'master_theme' — both accepted."""
        response = json.dumps({
            "theme": "SEO Domination",
            "derived_themes": [],
        })
        contract = validate_theme_plan_response(response)
        assert contract.master_theme == "SEO Domination"

    def test_derived_theme_with_filler_title_raises(self) -> None:
        """A derived theme whose title is conversational filler must fail."""
        response = json.dumps({
            "master_theme": "Content Growth",
            "derived_themes": [
                {"title": "I'm thrilled to present theme number one!"},
            ],
        })
        with pytest.raises(ResponseValidationError):
            validate_theme_plan_response(response)


# ---------------------------------------------------------------------------
# Workshop response validation
# ---------------------------------------------------------------------------

class TestValidateWorkshopResponse:
    """Customer scenario: DMA strategy workshop interaction."""

    def test_valid_workshop_response(self) -> None:
        """Well-formed workshop response passes validation."""
        payload = {
            "status": "discovery",
            "assistant_message": "Tell me about your target audience for this campaign.",
            "checkpoint_summary": "We have business basics, narrowing audience.",
            "next_step_options": ["Define audience", "Choose content angle"],
        }
        contract = validate_workshop_response(payload)
        assert contract.status == "discovery"
        assert "target audience" in contract.assistant_message

    def test_invalid_status_raises(self) -> None:
        """Unknown workshop status must be caught."""
        payload = {
            "status": "generating_magic",
            "assistant_message": "Working on it...",
        }
        with pytest.raises(ResponseValidationError):
            validate_workshop_response(payload)

    def test_empty_assistant_message_raises(self) -> None:
        """Empty assistant message must be caught."""
        payload = {
            "status": "discovery",
            "assistant_message": "",
        }
        with pytest.raises(ResponseValidationError):
            validate_workshop_response(payload)

    def test_filler_assistant_message_raises(self) -> None:
        """Conversational filler in assistant_message must be caught."""
        payload = {
            "status": "discovery",
            "assistant_message": "I'm thrilled to be working on your marketing strategy!",
        }
        with pytest.raises(ResponseValidationError):
            validate_workshop_response(payload)

    @pytest.mark.parametrize("status", [
        "discovery", "narrowing", "refining", "approval_ready", "approved", "draft_ready",
    ])
    def test_all_valid_statuses_accepted(self, status: str) -> None:
        """All defined workshop statuses must pass validation."""
        payload = {
            "status": status,
            "assistant_message": f"Current stage: {status}. What should we refine next?",
        }
        contract = validate_workshop_response(payload)
        assert contract.status == status


# ---------------------------------------------------------------------------
# Customer scenario: end-to-end DMA content calendar validation
# ---------------------------------------------------------------------------

class TestCustomerScenario:
    """
    Simulates: a WAOOAW customer on the CP portal asks the DMA to
    "show me a content calendar for my yoga studio".

    The backend LLM should return structured JSON with themes.
    These tests validate the response before it reaches the frontend.
    """

    def test_yoga_studio_theme_plan(self) -> None:
        """Customer: 'show me a content calendar for my yoga studio'"""
        llm_response = json.dumps({
            "master_theme": "Yoga Studio Growth",
            "derived_themes": [
                {"title": "Morning Routines", "description": "10-min sunrise yoga flows", "frequency": "weekly"},
                {"title": "Beginner Guides", "description": "Accessible yoga for newcomers", "frequency": "weekly"},
                {"title": "Teacher Spotlights", "description": "Instructor stories", "frequency": "bi-weekly"},
                {"title": "Client Testimonials", "description": "Real student stories", "frequency": "monthly"},
            ],
            "assistant_message": "Here is your content calendar with 4 themes. Review and approve to generate posts.",
        })

        contract = validate_theme_plan_response(llm_response, require_themes=True)

        assert contract.master_theme == "Yoga Studio Growth"
        assert len(contract.derived_themes) == 4
        assert all(t.title for t in contract.derived_themes)
        assert all(t.frequency for t in contract.derived_themes)

    def test_bridal_beauty_with_filler_blocked(self) -> None:
        """Customer asks for content — agent returns prose instead of themes."""
        filler_response = (
            "I'm thrilled to help you with your bridal beauty business! "
            "Let me create an amazing content calendar that will transform your social media presence!"
        )

        with pytest.raises(ResponseValidationError) as exc_info:
            validate_theme_plan_response(filler_response)

        # Filler was caught — the system would retry or use deterministic fallback
        assert any("filler" in v.rule for v in exc_info.value.violations)
