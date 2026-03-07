"""Unit tests for GoalSchedulerService using construct bindings (PLANT-MOULD-1 E2-S2)."""
import pytest

from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
from agent_mold.pump import BasePump
from agent_mold.spec import AgentSpec, ConstructBindings, ConstraintPolicy
from agent_mold.hooks import HookBus, HookStage, HookEvent


class SpyPump(BasePump):
    pulled = False

    async def pull(self, *, goal_config, hired_agent_id):
        SpyPump.pulled = True
        return {"spy": True}


class SpyProcessor(BaseProcessor):
    processed = False

    async def process(self, input_data: ProcessorInput, hook_bus: HookBus) -> ProcessorOutput:
        SpyProcessor.processed = True
        return ProcessorOutput(
            result="ok",
            metadata={},
            correlation_id=input_data.correlation_id,
        )


class FakeScheduler:
    pass


def make_spec_with_bindings() -> AgentSpec:
    return AgentSpec(
        agent_id="AGT-TEST-001",
        agent_type="test",
        bindings=ConstructBindings(
            processor_class=SpyProcessor,
            scheduler_class=FakeScheduler,
            pump_class=SpyPump,
        ),
    )


@pytest.mark.asyncio
async def test_scheduler_uses_pump_and_processor_from_bindings():
    """When agent_spec has bindings, _execute_goal dispatches via pump + processor."""
    # Reset spy flags
    SpyPump.pulled = False
    SpyProcessor.processed = False

    spec = make_spec_with_bindings()
    bus = HookBus()

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=bus)

    result = await scheduler._execute_goal(
        goal_instance_id="goal-123",
        correlation_id="corr-1",
        hired_agent_id="ha-1",
        goal_config={"key": "val"},
        agent_spec=spec,
    )

    assert SpyPump.pulled is True, "SpyPump.pull() was not called"
    assert SpyProcessor.processed is True, "SpyProcessor.process() was not called"
    assert result == "corr-1"


@pytest.mark.asyncio
async def test_pre_pump_and_pre_processor_hooks_fire():
    """PRE_PUMP, PRE_PROCESSOR, and POST_PROCESSOR hooks fire during execution."""
    SpyPump.pulled = False
    SpyProcessor.processed = False

    spec = make_spec_with_bindings()
    bus = HookBus()
    fired_stages = []

    class RecordHook:
        def handle(self, event: HookEvent):
            fired_stages.append(event.stage)
            return None

    bus.register(HookStage.PRE_PUMP, RecordHook())
    bus.register(HookStage.PRE_PROCESSOR, RecordHook())
    bus.register(HookStage.POST_PROCESSOR, RecordHook())

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService(hook_bus=bus)

    await scheduler._execute_goal(
        goal_instance_id="goal-456",
        correlation_id="corr-2",
        hired_agent_id="ha-2",
        goal_config={},
        agent_spec=spec,
    )

    assert HookStage.PRE_PUMP in fired_stages
    assert HookStage.PRE_PROCESSOR in fired_stages
    assert HookStage.POST_PROCESSOR in fired_stages


@pytest.mark.asyncio
async def test_legacy_path_when_no_bindings():
    """When agent_spec has no bindings, legacy path raises NotImplementedError."""
    spec = AgentSpec(agent_id="AGT-TEST-002", agent_type="legacy")

    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService()

    with pytest.raises(NotImplementedError):
        await scheduler._execute_goal(
            goal_instance_id="goal-789",
            agent_spec=spec,
        )


def test_scheduler_hook_bus_defaults_to_process_wide():
    """GoalSchedulerService uses default_hook_bus() when no hook_bus provided."""
    from services.goal_scheduler_service import GoalSchedulerService

    scheduler = GoalSchedulerService()
    # Accessing hook_bus should not raise
    bus = scheduler.hook_bus
    assert bus is not None
