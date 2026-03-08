"""components.py — BaseComponent ABC, ComponentInput/Output dataclasses, and component registry.

This single module combines what would be:
  components/base.py     — BaseComponent, ComponentInput, ComponentOutput (E3-S1)
  components/registry.py — register_component, get_component, list_registered (E3-S3)

Every execution component in the WAOOAW execution engine must subclass
BaseComponent and implement `execute()`. The `safe_execute()` wrapper handles
timing and exception conversion so callers never need try/except.

Import paths:
    from components import BaseComponent, ComponentInput, ComponentOutput
    from components import register_component, get_component, list_registered
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# E3-S1: Data classes
# ---------------------------------------------------------------------------

@dataclass
class ComponentInput:
    """Input payload for a single component execution step."""

    flow_run_id: str
    customer_id: str
    skill_config: dict[str, Any]
    run_context: dict[str, Any]
    previous_step_output: dict[str, Any] | None = None


@dataclass
class ComponentOutput:
    """Output (or error) from a single component execution step."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# E3-S1: BaseComponent ABC
# ---------------------------------------------------------------------------

class BaseComponent(ABC):
    """Stateless execution unit. Implement execute() in every subclass."""

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Unique string identifier, e.g. 'DeltaExchangePump'."""
        ...

    @abstractmethod
    async def execute(self, input: ComponentInput) -> ComponentOutput:
        """Execute component logic. Must be idempotent."""
        ...

    async def safe_execute(self, input: ComponentInput) -> ComponentOutput:
        """Wraps execute() with timing and exception catch."""
        start = time.monotonic()
        try:
            result = await self.execute(input)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except Exception as exc:
            return ComponentOutput(
                success=False,
                data={},
                error_message=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )


# ---------------------------------------------------------------------------
# E3-S3: Component registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, BaseComponent] = {}


def register_component(component: BaseComponent) -> None:
    """Register component instance under its component_type. Second registration overwrites."""
    _REGISTRY[component.component_type] = component


def get_component(component_type: str) -> BaseComponent:
    """Return the registered component instance for the given type.

    Raises:
        KeyError: if the component type is not registered. Message includes Available list.
    """
    if component_type not in _REGISTRY:
        raise KeyError(
            f"Component '{component_type}' not registered. "
            f"Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[component_type]


def list_registered() -> list[str]:
    """Return all currently registered component type identifiers."""
    return list(_REGISTRY.keys())
