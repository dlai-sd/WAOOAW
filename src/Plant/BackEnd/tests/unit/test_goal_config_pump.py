"""Unit tests for GoalConfigPump component (EXEC-ENGINE-001 E7-S1).

Tests:
  E7-S1-T1: run_context.goal_context with campaign_brief + two target_platforms
             → success=True, data["platform_specs"] has 2 entries
  E7-S1-T2: run_context.goal_context missing campaign_brief
             → success=False, error_message="campaign_brief required"
  E7-S1-T3: get_component("GoalConfigPump") after module import → returns instance
"""
from __future__ import annotations

import asyncio

import pytest

from components import ComponentInput, get_component


def _make_input(
    goal_context: dict | None = None,
    skill_config: dict | None = None,
) -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-gcp-001",
        customer_id="cust-001",
        skill_config=skill_config or {},
        run_context={"goal_context": goal_context or {}},
    )


@pytest.fixture(autouse=True)
def _ensure_goal_config_pump_registered():
    """Import module to trigger register_component() — makes tests order-independent."""
    from components import register_component
    import goal_config_pump as _mod

    register_component(_mod.GoalConfigPump())


@pytest.mark.unit
def test_goal_config_pump_success():
    """E7-S1-T1: campaign_brief + two target_platforms → success=True, 2 platform_specs."""
    from goal_config_pump import GoalConfigPump

    pump = GoalConfigPump()
    inp = _make_input(
        goal_context={"campaign_brief": "Promote our new AI product", "content_type": "post"},
        skill_config={
            "customer_fields": {
                "target_platforms": ["linkedin", "youtube"],
                "brand_name": "WAOOAW",
                "tone": "professional",
                "audience": "tech founders",
            }
        },
    )
    result = asyncio.run(pump.execute(inp))

    assert result.success is True
    assert len(result.data["platform_specs"]) == 2
    platforms = {spec["platform"] for spec in result.data["platform_specs"]}
    assert platforms == {"linkedin", "youtube"}
    assert result.data["brief_payload"]["campaign_brief"] == "Promote our new AI product"
    assert result.data["brief_payload"]["brand_name"] == "WAOOAW"


@pytest.mark.unit
def test_goal_config_pump_missing_brief():
    """E7-S1-T2: Missing campaign_brief → success=False, error_message set."""
    from goal_config_pump import GoalConfigPump

    pump = GoalConfigPump()
    inp = _make_input(goal_context={"content_type": "post"})
    result = asyncio.run(pump.execute(inp))

    assert result.success is False
    assert result.error_message == "campaign_brief required"


@pytest.mark.unit
def test_goal_config_pump_registered_after_import():
    """E7-S1-T3: get_component("GoalConfigPump") succeeds after module import."""
    comp = get_component("GoalConfigPump")
    assert comp.component_type == "GoalConfigPump"


@pytest.mark.unit
def test_goal_config_pump_default_platform():
    """Single target_platform defaults to linkedin when not specified in skill_config."""
    from goal_config_pump import GoalConfigPump

    pump = GoalConfigPump()
    inp = _make_input(
        goal_context={"campaign_brief": "Q1 campaign"},
        skill_config={"customer_fields": {}},
    )
    result = asyncio.run(pump.execute(inp))

    assert result.success is True
    assert len(result.data["platform_specs"]) == 1
    assert result.data["platform_specs"][0]["platform"] == "linkedin"
