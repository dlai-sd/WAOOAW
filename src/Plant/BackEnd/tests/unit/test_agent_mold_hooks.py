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
    assert denied.decision_id

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
    assert allowed.decision_id


def test_trading_actions_require_approval_id():
    bus = HookBus()
    bus.register(
        HookStage.PRE_TOOL_USE,
        ApprovalRequiredHook(actions_requiring_approval=["place_order", "close_position"]),
    )

    denied_place = bus.emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id="corr-3",
            agent_id="AGT-TRD-DELTA-001",
            customer_id="CUST-1",
            action="place_order",
            payload={},
        )
    )
    assert denied_place.allowed is False
    assert denied_place.reason == "approval_required"
    assert denied_place.decision_id

    allowed_close = bus.emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id="corr-4",
            agent_id="AGT-TRD-DELTA-001",
            customer_id="CUST-1",
            action="close_position",
            payload={"approval_id": "APR-456"},
        )
    )
    assert allowed_close.allowed is True
    assert allowed_close.decision_id
