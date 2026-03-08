"""Unit tests for components.py — BaseComponent ABC (EXEC-ENGINE-001 E3-S1).

Tests:
  E3-S1-T1: safe_execute() wraps a successful execute() → success=True, duration_ms >= 0
  E3-S1-T2: safe_execute() catches RuntimeError → success=False, error_message set
  E3-S1-T3: Instantiating BaseComponent directly raises TypeError
"""
from __future__ import annotations

import asyncio

import pytest

from components import BaseComponent, ComponentInput, ComponentOutput


# ---------------------------------------------------------------------------
# Concrete helpers
# ---------------------------------------------------------------------------

class _OkComponent(BaseComponent):
    @property
    def component_type(self) -> str:
        return "OkComponent"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        return ComponentOutput(success=True, data={"result": "ok"})


class _FailComponent(BaseComponent):
    @property
    def component_type(self) -> str:
        return "FailComponent"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        raise RuntimeError("boom")


def _make_input() -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-test-001",
        customer_id="cust-001",
        skill_config={},
        run_context={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_safe_execute_success():
    """E3-S1-T1: safe_execute() returns success=True, duration_ms >= 0."""
    comp = _OkComponent()
    result = asyncio.run(comp.safe_execute(_make_input()))
    assert result.success is True
    assert result.duration_ms >= 0
    assert result.error_message is None


@pytest.mark.unit
def test_safe_execute_catches_exception():
    """E3-S1-T2: safe_execute() catches RuntimeError, returns success=False."""
    comp = _FailComponent()
    result = asyncio.run(comp.safe_execute(_make_input()))
    assert result.success is False
    assert result.error_message == "boom"
    assert result.duration_ms >= 0


@pytest.mark.unit
def test_base_component_cannot_be_instantiated():
    """E3-S1-T3: Instantiating BaseComponent directly raises TypeError."""
    with pytest.raises(TypeError):
        BaseComponent()  # type: ignore[abstract]


@pytest.mark.unit
def test_component_input_fields():
    """ComponentInput stores all fields correctly."""
    inp = _make_input()
    assert inp.flow_run_id == "fr-test-001"
    assert inp.customer_id == "cust-001"
    assert inp.previous_step_output is None


@pytest.mark.unit
def test_component_output_default_fields():
    """ComponentOutput defaults are sensible."""
    out = ComponentOutput(success=True)
    assert out.data == {}
    assert out.error_message is None
    assert out.duration_ms == 0


@pytest.mark.unit
def test_safe_execute_sets_duration():
    """safe_execute() always sets duration_ms on the returned output."""
    comp = _OkComponent()
    result = asyncio.run(comp.safe_execute(_make_input()))
    assert isinstance(result.duration_ms, int)
    assert result.duration_ms >= 0
