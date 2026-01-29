from agent_mold.hooks import ApprovalRequiredHook, HookBus, HookEvent, HookStage


def test_publish_requires_approval_id():
    bus = HookBus()
    bus.register(HookStage.PRE_TOOL_USE, ApprovalRequiredHook(actions_requiring_approval=["publish"]))

    denied = bus.emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id="corr-1",
            agent_id="AGT-1",
            customer_id="CUST-1",
            action="publish",
            payload={},
        )
    )

    assert denied.allowed is False
    assert denied.reason == "approval_required"

    allowed = bus.emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id="corr-2",
            agent_id="AGT-1",
            customer_id="CUST-1",
            action="publish",
            payload={"approval_id": "APR-123"},
        )
    )

    assert allowed.allowed is True
