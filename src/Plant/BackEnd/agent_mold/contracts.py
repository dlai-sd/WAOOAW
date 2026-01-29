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
