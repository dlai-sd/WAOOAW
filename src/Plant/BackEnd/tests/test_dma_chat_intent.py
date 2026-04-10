"""Unit tests for DMA chat intent detection (fix/dma-chat-intent-to-action).

Tests cover _detect_generation_intent and _build_auto_draft in
digital_marketing_activation.py.
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from api.v1.digital_marketing_activation import _build_auto_draft, _detect_generation_intent
from agent_mold.skills.playbook import ArtifactType


# ---------------------------------------------------------------------------
# Approval-signal only (workshop is approval_ready)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phrase", [
    "yes",
    "approved",
    "looks good",
    "go ahead",
    "all set",
    "proceed",
    "sounds good",
    "let's go",
    "Yes, let's go",
    "Looks good to me!",
    "Great, proceed.",
    "Agreed.",
    "Perfect.",
])
def test_approval_signal_when_approval_ready_triggers_table(phrase: str) -> None:
    should_gen, arts = _detect_generation_intent(phrase, "approval_ready")
    assert should_gen is True
    assert ArtifactType.TABLE in arts


@pytest.mark.parametrize("phrase", [
    "yes",
    "confirms",
    "go ahead",
])
def test_approval_signal_when_approved_triggers_table(phrase: str) -> None:
    should_gen, arts = _detect_generation_intent(phrase, "approved")
    assert should_gen is True
    assert ArtifactType.TABLE in arts


def test_approval_does_not_trigger_when_workshop_not_ready() -> None:
    should_gen, _ = _detect_generation_intent("yes, looks good", "in_progress")
    assert should_gen is False


def test_empty_input_never_triggers() -> None:
    should_gen, arts = _detect_generation_intent("", "approval_ready")
    assert should_gen is False
    assert arts == []


def test_whitespace_only_never_triggers() -> None:
    should_gen, arts = _detect_generation_intent("   ", "approval_ready")
    assert should_gen is False
    assert arts == []


# ---------------------------------------------------------------------------
# Verb + artifact type — always triggers regardless of workshop status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phrase,expected_type", [
    ("show me a table", ArtifactType.TABLE),
    ("create a content calendar", ArtifactType.TABLE),
    ("generate a table", ArtifactType.TABLE),
    ("give me a schedule", ArtifactType.TABLE),
    # "tabular" must fire — real user phrasing confirmed in prod logs (Apr 2026)
    ("give me themes for April 2026, in tabular format", ArtifactType.TABLE),
    ("show me an image", ArtifactType.IMAGE),
    ("create a thumbnail", ArtifactType.IMAGE),
    ("generate a video", ArtifactType.VIDEO),
    ("make a reel", ArtifactType.VIDEO),
    ("produce a clip", ArtifactType.VIDEO),
    ("create audio narration", ArtifactType.AUDIO),
    ("make a podcast", ArtifactType.AUDIO),
    ("create a narrated video", ArtifactType.VIDEO_AUDIO),
    ("generate video with audio", ArtifactType.VIDEO_AUDIO),
])
def test_verb_plus_artifact_triggers(phrase: str, expected_type: ArtifactType) -> None:
    should_gen, arts = _detect_generation_intent(phrase, "in_progress")
    assert should_gen is True
    assert expected_type in arts


def test_artifact_mention_without_verb_and_no_approval() -> None:
    """Pure noun mention without action verb and no approval should not trigger."""
    should_gen, _ = _detect_generation_intent("I was thinking about a table", "in_progress")
    assert should_gen is False


def test_artifact_mention_with_approval_signal_triggers() -> None:
    """Artifact + approval signal (even without explicit generate verb) should trigger."""
    should_gen, arts = _detect_generation_intent("looks good, show me the video", "in_progress")
    assert should_gen is True
    assert ArtifactType.VIDEO in arts


# ---------------------------------------------------------------------------
# Multiple artifact types in one message
# ---------------------------------------------------------------------------


def test_multi_artifact_types() -> None:
    should_gen, arts = _detect_generation_intent("create an image and a video for me", "in_progress")
    assert should_gen is True
    assert ArtifactType.IMAGE in arts
    assert ArtifactType.VIDEO in arts


def test_approval_with_explicit_artifact_uses_explicit_not_default_table() -> None:
    should_gen, arts = _detect_generation_intent("yes, generate a video", "approval_ready")
    assert should_gen is True
    assert ArtifactType.VIDEO in arts
    # TABLE should not be the default when an explicit artifact type is present
    assert ArtifactType.TABLE not in arts


# ---------------------------------------------------------------------------
# Case-insensitivity
# ---------------------------------------------------------------------------


def test_case_insensitive_verb() -> None:
    should_gen, arts = _detect_generation_intent("SHOW ME A TABLE", "in_progress")
    assert should_gen is True
    assert ArtifactType.TABLE in arts


def test_case_insensitive_approval() -> None:
    should_gen, arts = _detect_generation_intent("YES", "approval_ready")
    assert should_gen is True


# ---------------------------------------------------------------------------
# _build_auto_draft — TABLE path regression tests
# ---------------------------------------------------------------------------

def _make_record(nickname: str = "Yogesh Khandge") -> MagicMock:
    r = MagicMock()
    r.nickname = nickname
    r.agent_id = "AGT-TEST-1"
    r.hired_instance_id = "HAI-TEST-1"
    r.customer_id = "CUST-TEST-1"
    return r


def test_build_auto_draft_table_produces_gfm_table() -> None:
    """TABLE artifact type must produce a GFM markdown table from derived_themes."""
    workspace = {
        "brand_name": "Beauty Artist",
        "location": "Pune",
        "campaign_setup": {
            "master_theme": "Natural Bridal Looks",
            "derived_themes": [
                {"title": "Bridal Prep", "description": "Tutorials for the big day", "frequency": "weekly"},
                {"title": "Affordable Glam", "description": "Budget beauty tips", "frequency": "bi-weekly"},
            ],
        },
    }
    result = asyncio.run(
        _build_auto_draft(
            record=_make_record(),
            workspace=workspace,
            master_theme="Natural Bridal Looks",
            campaign_id=None,
            artifact_types=[ArtifactType.TABLE],
            db=None,
        )
    )

    posts = result["posts"]
    assert len(posts) == 1
    p = posts[0]
    assert p["artifact_type"] == "table"
    # A GFM table must contain pipe characters
    assert "|" in p["text"]
    # Derived themes must be present
    assert "Bridal Prep" in p["text"]
    assert "Affordable Glam" in p["text"]


def test_build_auto_draft_table_no_agent_name_bleed() -> None:
    """Agent hire nickname must NEVER appear in generated table content or hashtags."""
    workspace = {
        "brand_name": "Sunrise Cafe",
        "campaign_setup": {
            "master_theme": "Coffee Culture",
            "derived_themes": [
                {"title": "Morning Rituals", "description": "Wake-up brews", "frequency": "daily"},
            ],
        },
    }
    result = asyncio.run(
        _build_auto_draft(
            record=_make_record(nickname="Yogesh Khandge"),
            workspace=workspace,
            master_theme="Coffee Culture",
            campaign_id=None,
            artifact_types=[ArtifactType.TABLE],
            db=None,
        )
    )

    posts = result["posts"]
    assert posts, "Expected at least one post"
    p = posts[0]
    assert "Yogesh" not in p["text"], "Agent first name must not appear in post text"
    assert "Khandge" not in p["text"], "Agent last name must not appear in post text"
    hashtags = p.get("hashtags") or []
    for tag in hashtags:
        assert "Yogesh" not in tag and "Khandge" not in tag, (
            f"Agent name found in hashtag: {tag}"
        )


def test_build_auto_draft_table_empty_themes_fallback() -> None:
    """When derived_themes is empty, a fallback single-row table is still produced."""
    workspace = {
        "brand_name": "TechStartup",
        "campaign_setup": {
            "master_theme": "Product Launch",
            "derived_themes": [],
        },
    }
    result = asyncio.run(
        _build_auto_draft(
            record=_make_record(),
            workspace=workspace,
            master_theme="Product Launch",
            campaign_id=None,
            artifact_types=[ArtifactType.TABLE],
            db=None,
        )
    )

    posts = result["posts"]
    assert len(posts) == 1
    assert posts[0]["artifact_type"] == "table"
    assert "|" in posts[0]["text"]
