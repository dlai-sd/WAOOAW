"""Unit tests for SkillRuntimeResolver (PLANT-RUNTIME-1 E1).

Tests cover:
- resolve_for_goal: happy path, missing goal, missing hired agent, missing spec
- resolve_for_hired_agent: happy path, missing hired agent, no agent_type_id
- goal_config is read from primary AgentSkillModel row
- goal_config defaults to {} when no primary skill row exists
"""
from __future__ import annotations

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_goal_row(goal_instance_id: str, hired_instance_id: str) -> MagicMock:
    row = MagicMock()
    row.goal_instance_id = goal_instance_id
    row.hired_instance_id = hired_instance_id
    return row


def _make_hired_row(
    hired_instance_id: str,
    agent_type_id: Optional[str],
    agent_id: Optional[str] = None,
) -> MagicMock:
    row = MagicMock()
    row.hired_instance_id = hired_instance_id
    row.agent_type_id = agent_type_id
    row.agent_id = agent_id
    return row


def _make_skill_row(goal_config: Optional[dict]) -> MagicMock:
    row = MagicMock()
    row.goal_config = goal_config
    return row


def _make_db(query_results: list) -> AsyncMock:
    """Build a fake AsyncSession that returns `query_results` in sequence."""
    db = AsyncMock()
    results = []
    for item in query_results:
        result = AsyncMock()
        result.scalar_one_or_none = AsyncMock(return_value=item)
        results.append(result)
    db.execute = AsyncMock(side_effect=results)
    return db


def _fake_agent_spec(agent_type_id: str, has_bindings: bool = True) -> MagicMock:
    spec = MagicMock()
    spec.agent_type = agent_type_id
    if has_bindings:
        bindings = MagicMock()
        spec.bindings = bindings
    else:
        spec.bindings = None
    return spec


def _fake_registry(agent_type_id: str, spec: Optional[MagicMock]) -> MagicMock:
    registry = MagicMock()
    registry.get_spec = MagicMock(return_value=spec)
    return registry


# ── resolve_for_goal ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_for_goal_happy_path():
    """Full chain resolves correctly: goal → hired → spec + goal_config."""
    import uuid
    agent_id_str = str(uuid.uuid4())
    goal_row = _make_goal_row("goal-1", "ha-1")
    hired_row = _make_hired_row("ha-1", "marketing", agent_id=agent_id_str)
    skill_row = _make_skill_row({"brand_name": "Acme"})

    db = _make_db([goal_row, hired_row, skill_row])
    spec = _fake_agent_spec("marketing")
    registry = _fake_registry("marketing", spec)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_goal("goal-1")

    assert bundle is not None
    assert bundle.agent_type_id == "marketing"
    assert bundle.hired_instance_id == "ha-1"
    assert bundle.agent_spec is spec
    assert bundle.goal_config == {"brand_name": "Acme"}


@pytest.mark.asyncio
async def test_resolve_for_goal_missing_goal_returns_none():
    """Returns None when goal_instance_id not found in DB."""
    db = _make_db([None])  # GoalInstanceModel not found

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    bundle = await resolver.resolve_for_goal("unknown-goal")

    assert bundle is None


@pytest.mark.asyncio
async def test_resolve_for_goal_missing_hired_agent_returns_none():
    """Returns None when hired agent is not found."""
    goal_row = _make_goal_row("goal-2", "ha-missing")
    db = _make_db([goal_row, None])  # HiredAgentModel not found

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    bundle = await resolver.resolve_for_goal("goal-2")

    assert bundle is None


@pytest.mark.asyncio
async def test_resolve_for_goal_no_agent_type_id_returns_none():
    """Returns None when hired agent has no agent_type_id."""
    goal_row = _make_goal_row("goal-3", "ha-3")
    hired_row = _make_hired_row("ha-3", agent_type_id=None, agent_id=None)
    db = _make_db([goal_row, hired_row])

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    bundle = await resolver.resolve_for_goal("goal-3")

    assert bundle is None


@pytest.mark.asyncio
async def test_resolve_for_goal_spec_not_in_registry_returns_none():
    """Returns None when AgentSpecRegistry does not know the agent_type_id."""
    import uuid
    goal_row = _make_goal_row("goal-4", "ha-4")
    hired_row = _make_hired_row("ha-4", "unknown_type", agent_id=str(uuid.uuid4()))
    db = _make_db([goal_row, hired_row])

    registry = _fake_registry("unknown_type", spec=None)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_goal("goal-4")

    assert bundle is None


@pytest.mark.asyncio
async def test_resolve_for_goal_no_primary_skill_defaults_empty_goal_config():
    """When no primary AgentSkillModel row exists, goal_config defaults to {}."""
    import uuid
    agent_id_str = str(uuid.uuid4())
    goal_row = _make_goal_row("goal-5", "ha-5")
    hired_row = _make_hired_row("ha-5", "tutor", agent_id=agent_id_str)
    skill_row = None  # No primary skill

    db = _make_db([goal_row, hired_row, skill_row])
    spec = _fake_agent_spec("tutor")
    registry = _fake_registry("tutor", spec)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_goal("goal-5")

    assert bundle is not None
    assert bundle.goal_config == {}


@pytest.mark.asyncio
async def test_resolve_for_goal_skill_row_null_goal_config_defaults_empty():
    """When primary skill row exists but goal_config is None, defaults to {}."""
    import uuid
    agent_id_str = str(uuid.uuid4())
    goal_row = _make_goal_row("goal-6", "ha-6")
    hired_row = _make_hired_row("ha-6", "trading", agent_id=agent_id_str)
    skill_row = _make_skill_row(None)  # goal_config is None

    db = _make_db([goal_row, hired_row, skill_row])
    spec = _fake_agent_spec("trading")
    registry = _fake_registry("trading", spec)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_goal("goal-6")

    assert bundle is not None
    assert bundle.goal_config == {}


# ── resolve_for_hired_agent ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_for_hired_agent_happy_path():
    """Direct hired_instance_id resolution succeeds."""
    import uuid
    agent_id_str = str(uuid.uuid4())
    hired_row = _make_hired_row("ha-10", "marketing", agent_id=agent_id_str)
    skill_row = _make_skill_row({"topic": "finance"})

    db = _make_db([hired_row, skill_row])
    spec = _fake_agent_spec("marketing")
    registry = _fake_registry("marketing", spec)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_hired_agent("ha-10")

    assert bundle is not None
    assert bundle.hired_instance_id == "ha-10"
    assert bundle.goal_config == {"topic": "finance"}


@pytest.mark.asyncio
async def test_resolve_for_hired_agent_missing_returns_none():
    """Returns None when hired_instance_id is not in DB."""
    db = _make_db([None])

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    bundle = await resolver.resolve_for_hired_agent("ha-missing")

    assert bundle is None


@pytest.mark.asyncio
async def test_resolve_for_hired_agent_no_agent_id_still_resolves():
    """When hired agent has no agent_id, goal_config is {} but spec still resolves."""
    hired_row = _make_hired_row("ha-11", "tutor", agent_id=None)
    db = _make_db([hired_row])  # No skill query needed — agent_id is None
    spec = _fake_agent_spec("tutor")
    registry = _fake_registry("tutor", spec)

    from services.skill_runtime_resolver import SkillRuntimeResolver

    resolver = SkillRuntimeResolver(db)
    with patch.object(resolver, "_spec_registry", return_value=registry):
        bundle = await resolver.resolve_for_hired_agent("ha-11")

    assert bundle is not None
    assert bundle.goal_config == {}
    assert bundle.agent_spec is spec


# ── SkillRuntimeBundle repr ───────────────────────────────────────────────────


def test_skill_runtime_bundle_repr():
    """__repr__ should not raise and include key info."""
    from services.skill_runtime_resolver import SkillRuntimeBundle

    spec = MagicMock()
    spec.bindings = MagicMock()
    bundle = SkillRuntimeBundle(
        agent_spec=spec,
        goal_config={},
        hired_instance_id="ha-repr",
        agent_type_id="marketing",
    )
    r = repr(bundle)
    assert "ha-repr" in r
    assert "marketing" in r
