"""Unit tests for AutonomousModeHook (ST-MVP-1 S9).

Tests:
  ST-S9-T1: Hook sets platform_approval_id when autonomous_mode=True + consent present
  ST-S9-T2: Hook is a no-op when autonomous_mode=False
  ST-S9-T3: Hook is a no-op when autonomous_consent_at is absent
"""
from __future__ import annotations

import asyncio

import pytest


@pytest.mark.unit
def test_hook_sets_platform_approval_when_consented():
    """ST-S9-T1: Hook sets platform_approval_id when autonomous_mode=True + consent set."""
    from agent_mold.hooks import AutonomousModeHook

    hook = AutonomousModeHook()
    context: dict = {
        "goal_config": {
            "customer_fields": {
                "autonomous_mode": True,
                "autonomous_consent_at": "2026-06-28T10:00:00+00:00",
            }
        }
    }
    asyncio.run(hook(context))
    assert "platform_approval_id" in context, "Expected platform_approval_id to be set"
    assert context["platform_approval_id"].startswith("AUTO-"), (
        f"Expected AUTO- prefix, got {context['platform_approval_id']}"
    )
    assert context.get("autonomous_execution") is True


@pytest.mark.unit
def test_hook_noop_when_autonomous_mode_false():
    """ST-S9-T2: Hook is no-op when autonomous_mode=False."""
    from agent_mold.hooks import AutonomousModeHook

    hook = AutonomousModeHook()
    context: dict = {
        "goal_config": {
            "customer_fields": {
                "autonomous_mode": False,
                "autonomous_consent_at": "2026-06-28T10:00:00+00:00",
            }
        }
    }
    asyncio.run(hook(context))
    assert "platform_approval_id" not in context
    assert "autonomous_execution" not in context


@pytest.mark.unit
def test_hook_noop_when_consent_absent():
    """ST-S9-T3: Hook is no-op when autonomous_consent_at is absent."""
    from agent_mold.hooks import AutonomousModeHook

    hook = AutonomousModeHook()
    context: dict = {
        "goal_config": {
            "customer_fields": {
                "autonomous_mode": True,
                # autonomous_consent_at intentionally missing
            }
        }
    }
    asyncio.run(hook(context))
    assert "platform_approval_id" not in context
    assert "autonomous_execution" not in context


@pytest.mark.unit
def test_hook_noop_when_goal_config_empty():
    """Hook is a no-op when goal_config is entirely absent."""
    from agent_mold.hooks import AutonomousModeHook

    hook = AutonomousModeHook()
    context: dict = {}
    asyncio.run(hook(context))
    assert "platform_approval_id" not in context


@pytest.mark.unit
def test_hook_registered_in_default_hook_bus():
    """AutonomousModeHook is registered at PRE_PUBLISH stage in default_hook_bus."""
    from agent_mold.enforcement import default_hook_bus
    from agent_mold.hooks import AutonomousModeHook, HookStage

    # Reset the lru_cache to get a fresh bus for this test
    default_hook_bus.cache_clear()
    bus = default_hook_bus()
    pre_publish_hooks = bus._hooks.get(HookStage.PRE_PUBLISH, [])
    autonomous_hooks = [h for h in pre_publish_hooks if isinstance(h, AutonomousModeHook)]
    assert len(autonomous_hooks) == 1, (
        f"Expected exactly 1 AutonomousModeHook at PRE_PUBLISH, found {len(autonomous_hooks)}"
    )
    # Clean up cache so other tests get a fresh bus
    default_hook_bus.cache_clear()
