"""Unit tests for components.py — component registry (EXEC-ENGINE-001 E3-S3).

Tests:
  E3-S3-T1: register + get by component_type returns the instance
  E3-S3-T2: get unknown type raises KeyError with 'Available:' in message
  E3-S3-T3: second registration overwrites first; list_registered() has one entry for that type
"""
from __future__ import annotations

import pytest

from components import (
    BaseComponent,
    ComponentInput,
    ComponentOutput,
    _REGISTRY,
    get_component,
    list_registered,
    register_component,
)


# ---------------------------------------------------------------------------
# Concrete helpers
# ---------------------------------------------------------------------------

class _MockComponent(BaseComponent):
    def __init__(self, ctype: str = "TestComp") -> None:
        self._ctype = ctype

    @property
    def component_type(self) -> str:
        return self._ctype

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        return ComponentOutput(success=True)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Isolate each test: clear the shared registry dict before and after."""
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_register_and_get():
    """E3-S3-T1: registered component is retrievable by component_type."""
    comp = _MockComponent("TestComp")
    register_component(comp)
    retrieved = get_component("TestComp")
    assert retrieved is comp


@pytest.mark.unit
def test_get_unknown_raises_key_error_with_available():
    """E3-S3-T2: KeyError message includes 'Available:' when type not registered."""
    with pytest.raises(KeyError) as exc_info:
        get_component("unknown")
    assert "Available:" in str(exc_info.value)


@pytest.mark.unit
def test_second_registration_overwrites():
    """E3-S3-T3: registering same type twice keeps only the second instance."""
    comp_a = _MockComponent("TestComp")
    comp_b = _MockComponent("TestComp")
    register_component(comp_a)
    register_component(comp_b)
    assert get_component("TestComp") is comp_b
    assert list_registered().count("TestComp") == 1


@pytest.mark.unit
def test_list_registered_empty():
    """list_registered() returns empty list when registry is empty."""
    assert list_registered() == []


@pytest.mark.unit
def test_list_registered_multiple():
    """list_registered() returns all registered type names."""
    register_component(_MockComponent("A"))
    register_component(_MockComponent("B"))
    names = list_registered()
    assert "A" in names
    assert "B" in names
    assert len(names) == 2
