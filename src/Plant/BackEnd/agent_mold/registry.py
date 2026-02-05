"""Dimension registry.

Chunk A: minimal registry that can validate and compile an AgentSpec.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from agent_mold.contracts import BasicDimension, DimensionContract, DimensionContext, RuntimeBundle
from agent_mold.spec import AgentSpec, CompiledAgentSpec, DimensionName


# Default null dimensions: include everything except skill.
# This keeps the compiled dimension set complete as DimensionName evolves.
DEFAULT_NULL_DIMENSIONS = [d for d in DimensionName if d is not DimensionName.SKILL]


class DimensionRegistry:
    def __init__(self, *, default_null_dimensions: Optional[Iterable[DimensionName]] = None):
        self._dimensions: Dict[DimensionName, DimensionContract] = {}
        self._default_null_dimensions = list(default_null_dimensions or DEFAULT_NULL_DIMENSIONS)

    def register(self, dimension: DimensionContract) -> None:
        self._dimensions[dimension.name] = dimension

    def compile(self, spec: AgentSpec) -> CompiledAgentSpec:
        compiled = CompiledAgentSpec.from_agent_spec(spec, default_null_dimensions=self._default_null_dimensions)

        # Validate only dimensions that are present=true (nulls are explicit safe defaults).
        for dim_name, dim_spec in compiled.dimensions.items():
            if not dim_spec.present:
                continue

            impl = self._dimensions.get(dim_name)
            if impl is None:
                # For Chunk A, unknown dimensions are not allowed.
                # If the spec has a dimension we don't implement, fail fast.
                raise ValueError(f"No implementation registered for dimension: {dim_name}")

            impl.validate(spec)

        return compiled

    def materialize(self, compiled: CompiledAgentSpec, *, context: Optional[DimensionContext] = None) -> RuntimeBundle:
        """Create runtime artifacts for a compiled spec."""

        if context is None:
            context = DimensionContext()

        artifacts: Dict[DimensionName, Dict[str, Any]] = {}
        for dim_name, dim_spec in compiled.dimensions.items():
            impl = self._dimensions.get(dim_name)
            if impl is None:
                if dim_spec.present:
                    raise ValueError(f"No implementation registered for dimension: {dim_name}")
                artifacts[dim_name] = {"present": False, "name": dim_name, "version": dim_spec.version, "config": {}}
                continue

            artifacts[dim_name] = impl.materialize(compiled, context)

        return RuntimeBundle(compiled=compiled, artifacts=artifacts)


def default_registry() -> DimensionRegistry:
    registry = DimensionRegistry()

    # Minimal implementations for all dimensions so reference agents compile.
    for dim_name in DimensionName:
        registry.register(BasicDimension(dim_name))

    return registry
