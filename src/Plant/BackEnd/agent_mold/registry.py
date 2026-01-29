"""Dimension registry.

Chunk A: minimal registry that can validate and compile an AgentSpec.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from agent_mold.contracts import DimensionContract, NullDimension
from agent_mold.spec import AgentSpec, CompiledAgentSpec, DimensionName


DEFAULT_NULL_DIMENSIONS = [
    DimensionName.INDUSTRY,
    DimensionName.TEAM,
    DimensionName.UI,
    DimensionName.LOCALIZATION,
]


class DimensionRegistry:
    def __init__(self, *, default_null_dimensions: Optional[Iterable[DimensionName]] = None):
        self._dimensions: Dict[DimensionName, DimensionContract] = {}
        self._default_null_dimensions = list(default_null_dimensions or DEFAULT_NULL_DIMENSIONS)

    def register(self, dimension: DimensionContract) -> None:
        self._dimensions[dimension.name] = dimension

    def compile(self, spec: AgentSpec) -> CompiledAgentSpec:
        compiled = CompiledAgentSpec.from_agent_spec(spec, default_null_dimensions=self._default_null_dimensions)

        # Validate only dimensions that are present=true (nulls validate trivially).
        for dim_name, dim_spec in compiled.dimensions.items():
            impl = self._dimensions.get(dim_name)
            if impl is None:
                # For Chunk A, unknown dimensions are not allowed.
                # If the spec has a dimension we don't implement, fail fast.
                if dim_spec.present:
                    raise ValueError(f"No implementation registered for dimension: {dim_name}")
                # If it's null/void, allow it.
                continue

            impl.validate(spec)

        return compiled


def default_registry() -> DimensionRegistry:
    registry = DimensionRegistry()

    # Register explicit NullDimensions for optional dimensions.
    for dim_name in DEFAULT_NULL_DIMENSIONS:
        registry.register(NullDimension(dim_name))

    return registry
