"""Unit tests for trigger_goal_run wiring with SkillRuntimeResolver.

PLANT-RUNTIME-1 E3 — verifies that the scheduler trigger API endpoint:
1. Constructs a SkillRuntimeResolver from the injected AsyncSession
2. Passes agent_spec + goal_config to run_goal_with_retry when bundle resolves
3. Falls back gracefully (passes None, None) when resolver returns None
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_bundle(agent_type_id: str = "marketing") -> MagicMock:
    """Build a fake SkillRuntimeBundle."""
    bundle = MagicMock()
    spec = MagicMock()
    spec.bindings = MagicMock()
    bundle.agent_spec = spec
    bundle.goal_config = {"brand": "WAOOAW"}
    bundle.agent_type_id = agent_type_id
    bundle.hired_instance_id = "ha-e3-1"
    return bundle


def _make_goal_run_result(status: str = "completed") -> MagicMock:
    """Build a fake GoalRunResult."""
    result = MagicMock()
    result.status = MagicMock()
    result.status.value = status
    result.error_message = None
    return result


# ── E3 tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trigger_passes_bundle_to_run_goal_when_resolved():
    """When resolver returns a bundle, run_goal_with_retry gets agent_spec + goal_config."""
    from api.v1.scheduler_admin import trigger_goal_run, TriggerGoalRequest

    bundle = _make_bundle()
    goal_run_result = _make_goal_run_result("completed")

    mock_admin_service = MagicMock()
    mock_admin_service.trigger_goal_run = AsyncMock(
        return_value={
            "status": "triggered",
            "message": "Goal run triggered by ops",
            "goal_instance_id": "goal-e3-1",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "operator": "ops",
        }
    )
    mock_admin_service.register_running_goal = MagicMock()
    mock_admin_service.unregister_running_goal = MagicMock()

    mock_scheduler = MagicMock()
    mock_scheduler.run_goal_with_retry = AsyncMock(return_value=goal_run_result)

    mock_db = AsyncMock()

    request = TriggerGoalRequest(operator="ops", scheduled_time=None)

    with patch(
        "api.v1.scheduler_admin.SkillRuntimeResolver"
    ) as MockResolver:
        mock_resolver_instance = MagicMock()
        mock_resolver_instance.resolve_for_goal = AsyncMock(return_value=bundle)
        MockResolver.return_value = mock_resolver_instance

        await trigger_goal_run(
            goal_instance_id="goal-e3-1",
            request=request,
            admin_service=mock_admin_service,
            scheduler_service=mock_scheduler,
            db=mock_db,
        )

    # Resolver was constructed with the injected db
    MockResolver.assert_called_once_with(mock_db)
    mock_resolver_instance.resolve_for_goal.assert_called_once_with("goal-e3-1")

    # run_goal_with_retry received agent_spec and goal_config from the bundle
    call_kwargs = mock_scheduler.run_goal_with_retry.call_args.kwargs
    assert call_kwargs["agent_spec"] is bundle.agent_spec
    assert call_kwargs["goal_config"] is bundle.goal_config


@pytest.mark.asyncio
async def test_trigger_falls_back_when_resolver_returns_none():
    """When resolver returns None, run_goal_with_retry is called with agent_spec=None."""
    from api.v1.scheduler_admin import trigger_goal_run, TriggerGoalRequest

    goal_run_result = _make_goal_run_result("completed")

    mock_admin_service = MagicMock()
    mock_admin_service.trigger_goal_run = AsyncMock(
        return_value={
            "status": "triggered",
            "message": "Goal run triggered by ops",
            "goal_instance_id": "goal-e3-2",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "operator": "ops",
        }
    )
    mock_admin_service.register_running_goal = MagicMock()
    mock_admin_service.unregister_running_goal = MagicMock()

    mock_scheduler = MagicMock()
    mock_scheduler.run_goal_with_retry = AsyncMock(return_value=goal_run_result)

    mock_db = AsyncMock()

    request = TriggerGoalRequest(operator="ops", scheduled_time=None)

    with patch(
        "api.v1.scheduler_admin.SkillRuntimeResolver"
    ) as MockResolver:
        mock_resolver_instance = MagicMock()
        mock_resolver_instance.resolve_for_goal = AsyncMock(return_value=None)
        MockResolver.return_value = mock_resolver_instance

        await trigger_goal_run(
            goal_instance_id="goal-e3-2",
            request=request,
            admin_service=mock_admin_service,
            scheduler_service=mock_scheduler,
            db=mock_db,
        )

    # run_goal_with_retry called with agent_spec=None, goal_config=None (legacy path)
    call_kwargs = mock_scheduler.run_goal_with_retry.call_args.kwargs
    assert call_kwargs["agent_spec"] is None
    assert call_kwargs["goal_config"] is None
