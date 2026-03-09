"""Unit tests for GoalSchedulerService with agent_spec + goal_config wiring.

PLANT-RUNTIME-1 E2 — verifies that run_goal_with_retry:
1. Accepts agent_spec and goal_config parameters
2. Passes them through to _execute_goal
3. The typed pump→processor path fires when agent_spec has bindings
4. Legacy path (NotImplementedError) fires when agent_spec is None
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_mold.hooks import HookBus
from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
from agent_mold.pump import BasePump
from agent_mold.spec import AgentSpec, ConstructBindings, ConstraintPolicy


# ── Spy constructs ────────────────────────────────────────────────────────────


class CapturePump(BasePump):
    last_goal_config: dict = {}

    async def pull(self, *, goal_config, hired_agent_id):
        CapturePump.last_goal_config = dict(goal_config)
        return goal_config


class CaptureProcessor(BaseProcessor):
    last_correlation_id: str = ""

    async def process(self, input_data: ProcessorInput, hook_bus) -> ProcessorOutput:
        CaptureProcessor.last_correlation_id = input_data.correlation_id
        return ProcessorOutput(
            result="ok",
            metadata={},
            correlation_id=input_data.correlation_id,
        )


class FakeScheduler:
    pass


def _make_spec() -> AgentSpec:
    return AgentSpec(
        agent_id="AGT-RUNTIME-TEST",
        agent_type="test_runtime",
        bindings=ConstructBindings(
            processor_class=CaptureProcessor,
            scheduler_class=FakeScheduler,
            pump_class=CapturePump,
        ),
        constraint_policy=ConstraintPolicy(),
    )


# ── E2 tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_goal_with_retry_passes_agent_spec_and_goal_config():
    """agent_spec + goal_config are forwarded to _execute_goal via the typed path."""
    CapturePump.last_goal_config = {}
    CaptureProcessor.last_correlation_id = ""

    spec = _make_spec()
    goal_config = {"brand": "WAOOAW", "channel": "linkedin"}

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=HookBus())

    result = await scheduler.run_goal_with_retry(
        goal_instance_id="goal-rt-1",
        scheduled_time=datetime.now(timezone.utc),
        hired_instance_id="ha-rt-1",
        correlation_id="corr-rt-1",
        agent_spec=spec,
        goal_config=goal_config,
    )

    # Typed path ran successfully
    assert CapturePump.last_goal_config == goal_config
    assert CaptureProcessor.last_correlation_id == "corr-rt-1"
    assert result.goal_instance_id == "goal-rt-1"


@pytest.mark.asyncio
async def test_run_goal_with_retry_default_goal_config_is_empty_dict():
    """When goal_config=None (default), pump receives {} — not None."""
    CapturePump.last_goal_config = {"old": "value"}

    spec = _make_spec()

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=HookBus())

    await scheduler.run_goal_with_retry(
        goal_instance_id="goal-rt-2",
        scheduled_time=datetime.now(timezone.utc),
        agent_spec=spec,
        # goal_config intentionally omitted → should default to None and be
        # passed as-is; _execute_goal normalises None to {}
    )

    # _execute_goal: `_goal_config: dict = goal_config or {}` → pump gets {}
    assert CapturePump.last_goal_config == {}


@pytest.mark.asyncio
async def test_run_goal_with_retry_no_agent_spec_raises_not_implemented():
    """When agent_spec is None (default), legacy path raises NotImplementedError."""
    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=HookBus())

    with pytest.raises(NotImplementedError):
        await scheduler.run_goal_with_retry(
            goal_instance_id="goal-rt-legacy",
            scheduled_time=datetime.now(timezone.utc),
        )


@pytest.mark.asyncio
async def test_run_goal_with_retry_agent_spec_without_bindings_raises_not_implemented():
    """An AgentSpec with bindings=None still uses the legacy path."""
    spec = AgentSpec(agent_id="AGT-NO-BINDINGS", agent_type="legacy_type")

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=HookBus())

    with pytest.raises(NotImplementedError):
        await scheduler.run_goal_with_retry(
            goal_instance_id="goal-rt-nobind",
            scheduled_time=datetime.now(timezone.utc),
            agent_spec=spec,
        )


@pytest.mark.asyncio
async def test_run_goal_with_retry_hired_instance_forwarded_to_execute_goal():
    """hired_instance_id is forwarded as hired_agent_id to _execute_goal."""
    # We test this by patching _execute_goal and verifying the kwarg
    spec = _make_spec()

    from services.goal_scheduler_service import GoalSchedulerService
    from unittest.mock import AsyncMock, patch

    scheduler = GoalSchedulerService(hook_bus=HookBus())

    with patch.object(
        scheduler, "_execute_goal", new_callable=AsyncMock, return_value="del-1"
    ) as mock_exec:
        await scheduler.run_goal_with_retry(
            goal_instance_id="goal-rt-3",
            scheduled_time=datetime.now(timezone.utc),
            hired_instance_id="ha-rt-3",
            correlation_id="corr-rt-3",
            agent_spec=spec,
            goal_config={"key": "val"},
        )

    mock_exec.assert_called_once_with(
        "goal-rt-3",
        "corr-rt-3",
        hired_agent_id="ha-rt-3",
        goal_config={"key": "val"},
        agent_spec=spec,
    )
