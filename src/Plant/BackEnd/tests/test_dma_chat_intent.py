"""Unit tests for DMA chat intent detection (fix/dma-chat-intent-to-action).

Tests cover _detect_generation_intent in digital_marketing_activation.py.
"""
from __future__ import annotations

import pytest

from api.v1.digital_marketing_activation import _detect_generation_intent
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
