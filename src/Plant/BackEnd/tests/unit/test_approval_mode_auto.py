"""Unit tests for approval_mode enforcement (PLANT-MOULD-1 E3-S1)."""
import pytest

from agent_mold.spec import ConstraintPolicy, ApprovalMode


def test_auto_mode_bypasses_approval():
    policy = ConstraintPolicy(approval_mode=ApprovalMode.AUTO)
    assert policy.approval_mode == ApprovalMode.AUTO


def test_manual_mode_requires_approval():
    policy = ConstraintPolicy(approval_mode=ApprovalMode.MANUAL)
    assert policy.approval_mode == ApprovalMode.MANUAL


def test_default_is_manual():
    policy = ConstraintPolicy()
    assert policy.approval_mode == ApprovalMode.MANUAL


@pytest.mark.asyncio
async def test_auto_mode_execute_goal_returns_deliverable_id():
    """AUTO approval mode: _execute_goal returns deliverable_id, not 'pending_review'."""
    from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
    from agent_mold.pump import BasePump
    from agent_mold.spec import AgentSpec, ConstructBindings
    from agent_mold.hooks import HookBus
    from services.goal_scheduler_service import GoalSchedulerService

    class AutoPump(BasePump):
        async def pull(self, *, goal_config, hired_agent_id):
            return {}

    class AutoProcessor(BaseProcessor):
        async def process(self, input_data: ProcessorInput, hook_bus) -> ProcessorOutput:
            return ProcessorOutput(result="done", metadata={},
                                   correlation_id=input_data.correlation_id)

    class FakeScheduler:
        pass

    spec = AgentSpec(
        agent_id="AGT-AUTO-001",
        agent_type="test",
        bindings=ConstructBindings(
            processor_class=AutoProcessor,
            scheduler_class=FakeScheduler,
            pump_class=AutoPump,
        ),
        constraint_policy=ConstraintPolicy(approval_mode=ApprovalMode.AUTO),
    )

    scheduler = GoalSchedulerService(hook_bus=HookBus())
    result = await scheduler._execute_goal(
        goal_instance_id="goal-auto-1",
        correlation_id="corr-auto-1",
        hired_agent_id="ha-auto-1",
        goal_config={},
        agent_spec=spec,
    )
    assert result == "corr-auto-1"


@pytest.mark.asyncio
async def test_manual_mode_with_blocking_hook_returns_pending_review():
    """MANUAL approval mode + blocking PRE_PUBLISH hook → 'pending_review'."""
    from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
    from agent_mold.pump import BasePump
    from agent_mold.spec import AgentSpec, ConstructBindings
    from agent_mold.hooks import HookBus, HookStage, HookEvent, HookDecision
    from services.goal_scheduler_service import GoalSchedulerService

    class ManualPump(BasePump):
        async def pull(self, *, goal_config, hired_agent_id):
            return {}

    class ManualProcessor(BaseProcessor):
        async def process(self, input_data: ProcessorInput, hook_bus) -> ProcessorOutput:
            return ProcessorOutput(result="done", metadata={},
                                   correlation_id=input_data.correlation_id)

    class FakeScheduler:
        pass

    class BlockingPublishHook:
        def handle(self, event: HookEvent):
            if event.stage == HookStage.PRE_PUBLISH and not event.payload.get("auto_mode"):
                return HookDecision(proceed=False, reason="approval_required")
            return None

    bus = HookBus()
    bus.register(HookStage.PRE_PUBLISH, BlockingPublishHook())

    spec = AgentSpec(
        agent_id="AGT-MANUAL-001",
        agent_type="test",
        bindings=ConstructBindings(
            processor_class=ManualProcessor,
            scheduler_class=FakeScheduler,
            pump_class=ManualPump,
        ),
        constraint_policy=ConstraintPolicy(approval_mode=ApprovalMode.MANUAL),
    )

    scheduler = GoalSchedulerService(hook_bus=bus)
    result = await scheduler._execute_goal(
        goal_instance_id="goal-manual-1",
        correlation_id="corr-manual-1",
        hired_agent_id="ha-manual-1",
        goal_config={},
        agent_spec=spec,
    )
    assert result == "pending_review"
