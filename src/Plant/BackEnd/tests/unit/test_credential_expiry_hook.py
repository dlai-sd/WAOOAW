"""Unit tests for CredentialExpiryHook (PLANT-MOULD-1 E3-S2)."""
import pytest
from datetime import datetime, timedelta, timezone

from agent_mold.hooks_builtin import CredentialExpiryHook
from agent_mold.hooks import HookEvent, HookStage


def make_event(connector_expires_at=None):
    payload = {}
    if connector_expires_at is not None:
        payload["connector_expires_at"] = connector_expires_at.isoformat()
    return HookEvent(
        stage=HookStage.PRE_PUMP,
        hired_agent_id="ha-1",
        agent_type="content_creator",
        payload=payload,
    )


def test_no_expiry_field_proceeds():
    hook = CredentialExpiryHook()
    decision = hook.handle(make_event())
    assert decision.proceed is True
    assert decision.reason == "no_expiry_field"


def test_expiry_far_future_proceeds():
    future = datetime.now(timezone.utc) + timedelta(days=30)
    hook = CredentialExpiryHook()
    decision = hook.handle(make_event(future))
    assert decision.proceed is True
    assert decision.reason == "credential_ok"


def test_expiry_within_7_days_warns_but_proceeds():
    soon = datetime.now(timezone.utc) + timedelta(days=3)
    hook = CredentialExpiryHook()
    decision = hook.handle(make_event(soon))
    assert decision.proceed is True
    assert decision.reason == "credential_expiring_soon"
    assert decision.metadata is not None
    assert decision.metadata["days_left"] == 3


def test_already_expired_warns_and_proceeds():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    hook = CredentialExpiryHook()
    decision = hook.handle(make_event(past))
    assert decision.proceed is True  # still True — caller decides to halt
    assert decision.reason == "credential_expiring_soon"


def test_invalid_expiry_format_proceeds():
    event = HookEvent(
        stage=HookStage.PRE_PUMP,
        hired_agent_id="ha-2",
        agent_type="trading",
        payload={"connector_expires_at": "not-a-date"},
    )
    hook = CredentialExpiryHook()
    decision = hook.handle(event)
    assert decision.proceed is True
    assert decision.reason == "invalid_expiry_format"


def test_expiry_exactly_7_days_warns():
    """Boundary: exactly 7 days left should trigger the warning."""
    exactly_7 = datetime.now(timezone.utc) + timedelta(days=7, hours=1)
    hook = CredentialExpiryHook()
    # Should be > 7 days, no warning
    decision = hook.handle(make_event(exactly_7))
    assert decision.proceed is True
    assert decision.reason == "credential_ok"


def test_credential_expiry_hook_registered_in_default_bus():
    """CredentialExpiryHook is registered on PRE_PUMP in default_hook_bus()."""
    from agent_mold.enforcement import default_hook_bus
    from agent_mold.hooks import HookStage

    # Reset lru_cache so we get a fresh bus (important if other tests ran first)
    default_hook_bus.cache_clear()
    bus = default_hook_bus()
    pre_pump_hooks = bus._hooks.get(HookStage.PRE_PUMP, [])
    hook_types = [type(h).__name__ for h in pre_pump_hooks]
    assert "CredentialExpiryHook" in hook_types
    default_hook_bus.cache_clear()
