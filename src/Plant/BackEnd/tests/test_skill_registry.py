"""Tests for Skill Registry — PLANT-CONTENT-1 Iteration 4, Epic E7.

Validates:
- content.creator.v1 registered in skill_registry
- content.publisher.v1 registered in skill_registry
- SkillCategory.CONTENT exists in playbook.py
- Existing DimensionRegistry is unchanged

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/test_skill_registry.py -v
"""
from __future__ import annotations

import pytest

from agent_mold.registry import SkillRegistry, SkillRegistryEntry, skill_registry
from agent_mold.skills.playbook import SkillCategory


# ─── E7-S1: content.creator.v1 registered ────────────────────────────────────

@pytest.mark.unit
def test_skill_registry_content_creator_registered():
    """E7-S1: skill_registry.get('content.creator.v1') returns a SkillRegistryEntry."""
    entry = skill_registry.get("content.creator.v1")
    assert entry is not None
    assert isinstance(entry, SkillRegistryEntry)
    assert entry.skill_id == "content.creator.v1"
    assert entry.name == "Content Creator"
    assert entry.category == SkillCategory.CONTENT
    assert entry.version == "1.0.0"


@pytest.mark.unit
def test_skill_registry_content_creator_optional_keys():
    """content.creator.v1 has expected optional config keys."""
    entry = skill_registry.get("content.creator.v1")
    assert entry is not None
    assert "executor_backend" in entry.optional_config_keys
    assert "xai_api_key" in entry.optional_config_keys
    assert entry.required_config_keys == []


# ─── E7-S1: content.publisher.v1 registered ──────────────────────────────────

@pytest.mark.unit
def test_skill_registry_content_publisher_registered():
    """E7-S1: skill_registry.get('content.publisher.v1') returns a SkillRegistryEntry."""
    entry = skill_registry.get("content.publisher.v1")
    assert entry is not None
    assert isinstance(entry, SkillRegistryEntry)
    assert entry.skill_id == "content.publisher.v1"
    assert entry.name == "Content Publisher"
    assert entry.category == SkillCategory.CONTENT
    assert entry.version == "1.0.0"


@pytest.mark.unit
def test_skill_registry_content_publisher_optional_keys():
    """content.publisher.v1 has expected optional config keys."""
    entry = skill_registry.get("content.publisher.v1")
    assert entry is not None
    assert "destination_type" in entry.optional_config_keys
    assert "credential_ref" in entry.optional_config_keys
    assert entry.required_config_keys == []


# ─── SkillCategory.CONTENT exists ────────────────────────────────────────────

@pytest.mark.unit
def test_skill_category_content_exists():
    """SkillCategory.CONTENT is defined in playbook.py."""
    assert SkillCategory.CONTENT == "content"


# ─── Unknown skill_id returns None ───────────────────────────────────────────

@pytest.mark.unit
def test_skill_registry_unknown_skill_returns_none():
    """skill_registry.get('nonexistent.skill') returns None — does not raise."""
    result = skill_registry.get("nonexistent.skill")
    assert result is None


# ─── list_all includes both content skills ────────────────────────────────────

@pytest.mark.unit
def test_skill_registry_list_all_includes_content_skills():
    """skill_registry.list_all() includes both content skills."""
    all_ids = {e.skill_id for e in skill_registry.list_all()}
    assert "content.creator.v1" in all_ids
    assert "content.publisher.v1" in all_ids


# ─── is_registered helper ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_skill_registry_is_registered():
    """is_registered returns True for known skills, False for unknown."""
    assert skill_registry.is_registered("content.creator.v1") is True
    assert skill_registry.is_registered("content.publisher.v1") is True
    assert skill_registry.is_registered("does.not.exist") is False


# ─── DimensionRegistry unchanged ─────────────────────────────────────────────

@pytest.mark.unit
def test_dimension_registry_unchanged():
    """DimensionRegistry default_registry() compiles correctly (existing behaviour)."""
    from agent_mold.registry import default_registry
    registry = default_registry()
    # The registry must be non-empty (all DimensionNames registered)
    from agent_mold.spec import DimensionName
    for dim in DimensionName:
        assert registry._dimensions.get(dim) is not None


# ─── Fresh SkillRegistry (independent) ───────────────────────────────────────

@pytest.mark.unit
def test_skill_registry_fresh_instance_is_empty():
    """A fresh SkillRegistry() starts empty — module singleton is separate."""
    fresh = SkillRegistry()
    assert fresh.list_all() == []
    assert fresh.get("content.creator.v1") is None


@pytest.mark.unit
def test_skill_registry_entry_serializes_to_json():
    """SkillRegistryEntry.model_dump_json() works without error."""
    entry = skill_registry.get("content.creator.v1")
    assert entry is not None
    json_str = entry.model_dump_json()
    assert "content.creator.v1" in json_str
    assert "CONTENT" in json_str.upper() or "content" in json_str
