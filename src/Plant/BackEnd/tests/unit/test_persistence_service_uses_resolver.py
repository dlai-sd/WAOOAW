"""Unit tests for SchedulerPersistenceService with SkillRuntimeResolver wiring.

PLANT-RUNTIME-1 E4 — verifies that _replay_missed_run:
1. Calls resolver.resolve_for_goal when a resolver is injected
2. Passes agent_spec + goal_config to run_goal_with_retry when bundle resolves
3. Falls back to agent_spec=None / goal_config=None when resolver returns None
4. Behaves identically to pre-E4 (no resolver) when resolver is not provided
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from models.scheduled_goal_run import ScheduledGoalRunModel
from services.scheduler_persistence_service import (
    RecoveryResult,
    SchedulerPersistenceService,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_scheduled_run(
    goal_instance_id: str = "goal-e4-1",
    hired_instance_id: str = "ha-e4-1",
) -> ScheduledGoalRunModel:
    run = ScheduledGoalRunModel.create_scheduled_run(
        scheduled_run_id=f"sched_{goal_instance_id}",
        goal_instance_id=goal_instance_id,
        scheduled_time=datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
        hired_instance_id=hired_instance_id,
    )
    return run


def _make_bundle(agent_type_id: str = "marketing") -> MagicMock:
    bundle = MagicMock()
    spec = MagicMock()
    spec.bindings = MagicMock()
    bundle.agent_spec = spec
    bundle.goal_config = {"brand": "WAOOAW"}
    bundle.agent_type_id = agent_type_id
    return bundle


def _make_scheduler_service() -> MagicMock:
    svc = MagicMock()
    svc.run_goal_with_retry = AsyncMock(return_value=MagicMock())
    return svc


def _make_resolver(bundle) -> MagicMock:
    resolver = MagicMock()
    resolver.resolve_for_goal = AsyncMock(return_value=bundle)
    return resolver


def _make_persistence_service(
    resolver=None, scheduler_service=None
) -> SchedulerPersistenceService:
    db = Mock()
    svc = SchedulerPersistenceService(
        db=db,
        scheduler_service=scheduler_service or _make_scheduler_service(),
        resolver=resolver,
    )
    # Stub out repos so we don't hit DB
    svc.scheduled_run_repo = Mock()
    svc.scheduled_run_repo.update = Mock()
    svc.goal_run_repo = Mock()
    return svc


# ── E4 tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_replay_passes_bundle_to_run_goal_when_resolver_resolves():
    """When resolver returns a bundle, run_goal_with_retry gets agent_spec + goal_config."""
    bundle = _make_bundle()
    resolver = _make_resolver(bundle)
    scheduler_service = _make_scheduler_service()
    svc = _make_persistence_service(resolver=resolver, scheduler_service=scheduler_service)

    scheduled_run = _make_scheduled_run("goal-e4-1", "ha-e4-1")
    result = RecoveryResult()

    await svc._replay_missed_run(scheduled_run, result)

    resolver.resolve_for_goal.assert_called_once_with("goal-e4-1")

    call_kwargs = scheduler_service.run_goal_with_retry.call_args.kwargs
    assert call_kwargs["agent_spec"] is bundle.agent_spec
    assert call_kwargs["goal_config"] is bundle.goal_config
    assert call_kwargs["goal_instance_id"] == "goal-e4-1"
    assert call_kwargs["hired_instance_id"] == "ha-e4-1"


@pytest.mark.asyncio
async def test_replay_falls_back_when_resolver_returns_none():
    """When resolver returns None, run_goal_with_retry called with agent_spec=None."""
    resolver = _make_resolver(bundle=None)
    scheduler_service = _make_scheduler_service()
    svc = _make_persistence_service(resolver=resolver, scheduler_service=scheduler_service)

    scheduled_run = _make_scheduled_run("goal-e4-2", "ha-e4-2")
    result = RecoveryResult()

    await svc._replay_missed_run(scheduled_run, result)

    resolver.resolve_for_goal.assert_called_once_with("goal-e4-2")

    call_kwargs = scheduler_service.run_goal_with_retry.call_args.kwargs
    assert call_kwargs["agent_spec"] is None
    assert call_kwargs["goal_config"] is None


@pytest.mark.asyncio
async def test_replay_no_resolver_behaves_as_before():
    """When no resolver is provided, _replay_missed_run behaves identically to pre-E4."""
    scheduler_service = _make_scheduler_service()
    # resolver=None (default) — no resolver injected
    svc = _make_persistence_service(resolver=None, scheduler_service=scheduler_service)

    scheduled_run = _make_scheduled_run("goal-e4-3", "ha-e4-3")
    result = RecoveryResult()

    await svc._replay_missed_run(scheduled_run, result)

    call_kwargs = scheduler_service.run_goal_with_retry.call_args.kwargs
    assert call_kwargs["agent_spec"] is None
    assert call_kwargs["goal_config"] is None
    assert call_kwargs["goal_instance_id"] == "goal-e4-3"


@pytest.mark.asyncio
async def test_persistence_service_accepts_resolver_in_constructor():
    """SchedulerPersistenceService __init__ accepts resolver parameter."""
    db = Mock()
    mock_resolver = MagicMock()

    svc = SchedulerPersistenceService(db=db, resolver=mock_resolver)

    assert svc.resolver is mock_resolver


def test_persistence_service_resolver_defaults_to_none():
    """When resolver is omitted, it defaults to None (backward compatible)."""
    db = Mock()
    svc = SchedulerPersistenceService(db=db)
    assert svc.resolver is None
