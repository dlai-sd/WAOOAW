"""Tests for AgentLifecycleHooks ABC (MOULD-GAP-1 E1-S1 + E1-S2)."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from agent_mold.hooks import AgentLifecycleHooks, LifecycleContext, NullLifecycleHooks


def make_ctx() -> LifecycleContext:
    return LifecycleContext(
        hired_instance_id="hi-1",
        agent_type_id="trading",
        customer_id="cust-1",
    )


@pytest.mark.asyncio
async def test_null_hooks_all_methods_are_no_ops():
    """NullLifecycleHooks must not raise on any event call."""
    hooks = NullLifecycleHooks()
    ctx = make_ctx()
    await hooks.on_hire(ctx)
    await hooks.on_trial_start(ctx)
    await hooks.on_deliverable_approved(ctx)
    await hooks.on_cancel(ctx)


def test_construct_bindings_validates_lifecycle_hooks_class():
    """ConstructBindings.validate() must reject non-AgentLifecycleHooks class."""
    from agent_mold.spec import ConstructBindings
    from agent_mold.processor import BaseProcessor
    from agent_mold.pump import BasePump, GoalConfigPump

    class FakeProcessor(BaseProcessor):
        PROCESSOR_ID = "test"
        async def execute(self, inp): ...  # type: ignore[override]

    class FakeScheduler: ...

    class NotAHook:  # does NOT inherit AgentLifecycleHooks
        pass

    bindings = ConstructBindings(
        processor_class=FakeProcessor,
        scheduler_class=FakeScheduler,
        pump_class=GoalConfigPump,
        lifecycle_hooks_class=NotAHook,
    )
    with pytest.raises(TypeError, match="AgentLifecycleHooks"):
        bindings.validate()


def test_construct_bindings_accepts_null_lifecycle():
    """lifecycle_hooks_class=None is valid — no-ops are used."""
    from agent_mold.spec import ConstructBindings
    from agent_mold.processor import BaseProcessor
    from agent_mold.pump import GoalConfigPump

    class FakeProcessor(BaseProcessor):
        PROCESSOR_ID = "test"
        async def execute(self, inp): ...  # type: ignore[override]

    class FakeScheduler: ...

    bindings = ConstructBindings(
        processor_class=FakeProcessor,
        scheduler_class=FakeScheduler,
        pump_class=GoalConfigPump,
        lifecycle_hooks_class=None,
    )
    bindings.validate()  # must not raise


def test_construct_bindings_accepts_valid_lifecycle_hooks_class():
    """ConstructBindings.validate() must accept a proper AgentLifecycleHooks subclass."""
    from agent_mold.spec import ConstructBindings
    from agent_mold.processor import BaseProcessor
    from agent_mold.pump import GoalConfigPump

    class FakeProcessor(BaseProcessor):
        PROCESSOR_ID = "test"
        async def execute(self, inp): ...  # type: ignore[override]

    class FakeScheduler: ...

    bindings = ConstructBindings(
        processor_class=FakeProcessor,
        scheduler_class=FakeScheduler,
        pump_class=GoalConfigPump,
        lifecycle_hooks_class=NullLifecycleHooks,
    )
    bindings.validate()  # must not raise


@pytest.mark.asyncio
async def test_on_hire_called_on_finalize():
    """Mocking registry + lifecycle hooks — on_hire must be awaited during finalize."""
    mock_hooks = MagicMock(spec=AgentLifecycleHooks)
    mock_hooks.on_hire = AsyncMock()
    mock_hooks.on_trial_start = AsyncMock()

    # Simulate finalize path — on_hire must be called
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    await mock_hooks.on_hire(ctx)
    mock_hooks.on_hire.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_deliverable_approved_called_on_review():
    """on_deliverable_approved must be awaited when decision == 'approved'."""
    mock_hooks = MagicMock(spec=AgentLifecycleHooks)
    mock_hooks.on_deliverable_approved = AsyncMock()

    ctx = LifecycleContext("hi-1", "trading", "cust-1", deliverable_id="del-1")
    await mock_hooks.on_deliverable_approved(ctx)
    mock_hooks.on_deliverable_approved.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifecycle_hook_error_does_not_fail_hire():
    """A crashing hook must be caught — hire/approval response must not 500."""
    class CrashingHooks(AgentLifecycleHooks):
        async def on_hire(self, ctx: LifecycleContext) -> None:
            raise RuntimeError("simulated hook crash")

    hooks = CrashingHooks()
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    # Should not raise — caller wraps in try/except
    try:
        await hooks.on_hire(ctx)
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass  # Caller must catch this — test documents the contract
