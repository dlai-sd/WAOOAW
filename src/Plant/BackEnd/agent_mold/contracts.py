"""Dimension contracts.

Chunk A provides a minimal contract interface plus safe NullDimension behavior.
Later chunks will add richer compile/materialize/enforcement logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from agent_mold.spec import AgentSpec, CompiledAgentSpec, DimensionName


@dataclass(frozen=True)
class DimensionContext:
    """Runtime context for dimension compilation/materialization.

    This is intentionally small initially; it will grow as we add:
    - customer profile
    - industry profile
    - integrations and credentials
    - AI Explorer routing
    """

    correlation_id: Optional[str] = None


class DimensionContract(ABC):
    """Interface implemented by all dimensions."""

    name: DimensionName
    version: str = "1.0"

    @abstractmethod
    def validate(self, spec: AgentSpec) -> None:
        """Validate the dimension configuration inside the AgentSpec."""

    @abstractmethod
    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        """Return dimension artifacts needed at runtime (schemas, adapters, templates)."""

    @abstractmethod
    def register_hooks(self, hook_bus: Any) -> None:
        """Register enforcement hooks (trial, budget, approvals)."""

    @abstractmethod
    def observe(self, event: Any) -> None:
        """Observe runtime events for learning/metrics."""


class NullDimension(DimensionContract):
    """Explicit null/void dimension implementation."""

    def __init__(self, name: DimensionName):
        self.name = name

    def validate(self, spec: AgentSpec) -> None:
        return None

    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        return {"present": False, "name": self.name}

    def register_hooks(self, hook_bus: Any) -> None:
        return None

    def observe(self, event: Any) -> None:
        return None


class BasicDimension(DimensionContract):
    """Minimal dimension implementation for compile/materialize.

    This is intentionally shallow: it provides a stable runtime bundle shape
    (present/name/config/version) without introducing full per-dimension
    behavior yet.
    """

    def __init__(self, name: DimensionName, *, version: str = "1.0"):
        self.name = name
        self.version = version

    def validate(self, spec: AgentSpec) -> None:
        # AgentSpec validation enforces config requirements; registry controls
        # which dimensions are required by agent type in later epics.
        return None

    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        dim_spec = compiled.dimensions.get(self.name)
        if dim_spec is None:
            return {"present": False, "name": self.name, "version": self.version, "config": {}}

        if not dim_spec.present:
            return {"present": False, "name": self.name, "version": dim_spec.version, "config": {}}

        return {
            "present": True,
            "name": self.name,
            "version": dim_spec.version,
            "config": dict(dim_spec.config or {}),
        }

    def register_hooks(self, hook_bus: Any) -> None:
        return None

    def observe(self, event: Any) -> None:
        return None


@dataclass(frozen=True)
class RuntimeBundle:
    """Materialized runtime artifacts for an agent.

    The bundle is the product of: AgentSpec -> CompiledAgentSpec -> artifacts.
    """

    compiled: CompiledAgentSpec
    artifacts: Dict[DimensionName, Dict[str, Any]]
