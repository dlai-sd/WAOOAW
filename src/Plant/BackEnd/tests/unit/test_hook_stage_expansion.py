"""Unit tests for HookStage expansion (PLANT-MOULD-1 E2-S1)."""
from agent_mold.hooks import HookStage, HookBus, HookEvent, HookDecision


def test_all_new_stages_exist():
    stage_values = [s.value for s in HookStage]
    for stage in [
        "pre_pump", "post_pump", "pre_processor", "post_processor",
        "pre_publish", "post_publish",
    ]:
        assert stage in stage_values, f"Missing HookStage value: {stage}"


def test_all_original_stages_preserved():
    stage_values = [s.value for s in HookStage]
    for stage in ["session_start", "pre_skill", "pre_tool_use", "post_tool_use", "post_skill", "session_end"]:
        assert stage in stage_values, f"Original stage removed: {stage}"


def test_hook_stages_are_unique():
    values = [s.value for s in HookStage]
    assert len(values) == len(set(values)), "Duplicate HookStage values found"


def test_register_and_emit_pre_pump():
    bus = HookBus()
    received = []

    class RecordHook:
        def handle(self, event: HookEvent):
            received.append(event.stage)
            return None

    bus.register(HookStage.PRE_PUMP, RecordHook())
    bus.emit(HookEvent(stage=HookStage.PRE_PUMP, hired_agent_id="ha-1", agent_type="test", payload={}))
    assert HookStage.PRE_PUMP in received


def test_pre_publish_hook_can_halt():
    bus = HookBus()

    class HaltHook:
        def handle(self, event: HookEvent):
            return HookDecision(proceed=False, reason="test halt")

    bus.register(HookStage.PRE_PUBLISH, HaltHook())
    decision = bus.emit(
        HookEvent(stage=HookStage.PRE_PUBLISH, hired_agent_id="ha-1", agent_type="test", payload={})
    )
    assert decision.proceed is False
    assert decision.allowed is False


def test_emit_allows_when_no_hooks_registered():
    bus = HookBus()
    decision = bus.emit(
        HookEvent(stage=HookStage.POST_PUMP, hired_agent_id="ha-1", agent_type="test", payload={})
    )
    assert decision.allowed is True
    assert decision.proceed is True


def test_pre_processor_hook_fires():
    bus = HookBus()
    received = []

    class RecordHook:
        def handle(self, event: HookEvent):
            received.append(event.stage)
            return None

    bus.register(HookStage.PRE_PROCESSOR, RecordHook())
    bus.emit(HookEvent(stage=HookStage.PRE_PROCESSOR, hired_agent_id="ha-2", agent_type="trading"))
    assert HookStage.PRE_PROCESSOR in received


def test_existing_pre_tool_use_hook_still_works():
    """Ensure backward-compat: old PRE_TOOL_USE stage still dispatches."""
    bus = HookBus()
    received = []

    class RecordHook:
        def handle(self, event: HookEvent):
            received.append(event.stage)
            return None

    bus.register(HookStage.PRE_TOOL_USE, RecordHook())
    bus.emit(HookEvent(
        stage=HookStage.PRE_TOOL_USE,
        correlation_id="corr-1",
        agent_id="AGT-1",
        payload={},
    ))
    assert HookStage.PRE_TOOL_USE in received


def test_hook_decision_allowed_and_proceed_are_synced():
    d1 = HookDecision(allowed=True, reason="ok")
    assert d1.proceed is True

    d2 = HookDecision(allowed=False, reason="denied")
    assert d2.proceed is False

    d3 = HookDecision(proceed=True, reason="ok")
    assert d3.allowed is True

    d4 = HookDecision(proceed=False, reason="denied")
    assert d4.allowed is False
