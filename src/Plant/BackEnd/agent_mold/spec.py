"""AgentSpec and dimension specs.

Design intent:
- Agents are manufactured from a declarative AgentSpec.
- Capabilities are attached as dimensions (skill/industry/team/etc.).
- Dimensions may be present or null/void (explicit).

This is intentionally minimal in Chunk A; later chunks will add richer validation
and compilation steps.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, Field, root_validator


class DimensionName(str, Enum):
    SKILL = "skill"
    INDUSTRY = "industry"
    TEAM = "team"
    INTEGRATIONS = "integrations"
    UI = "ui"
    LOCALIZATION = "localization"
    TRIAL = "trial"
    BUDGET = "budget"


class DimensionSpec(BaseModel):
    """Configuration for a single dimension.

    `present=false` means the dimension is intentionally null/void.
    """

    name: DimensionName = Field(..., description="Dimension name")
    present: bool = Field(True, description="Whether this dimension is enabled")
    version: str = Field("1.0", description="Dimension contract version")
    config: Dict[str, Any] = Field(default_factory=dict, description="Dimension configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "industry",
                "present": False,
                "version": "1.0",
                "config": {},
            }
        }


class AgentSpec(BaseModel):
    """Declarative agent blueprint."""

    agent_id: str = Field(..., min_length=1, description="Stable agent identifier")
    agent_type: str = Field(..., min_length=1, description="Agent type (e.g., marketing, tutor)")
    version: str = Field("1.0", description="AgentSpec version")

    # Dimensions are supplied as a mapping so config can be concise.
    # Example: {"industry": {"present": false}}
    dimensions: Dict[DimensionName, DimensionSpec] = Field(
        default_factory=dict,
        description="Attached dimensions (explicit present or null/void)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "AGT-MARKETING-001",
                "agent_type": "marketing",
                "version": "1.0",
                "dimensions": {
                    "skill": {"name": "skill", "present": True, "version": "1.0", "config": {}},
                    "industry": {"name": "industry", "present": False, "version": "1.0", "config": {}},
                },
            }
        }

    @root_validator(pre=True)
    def _normalize_dimensions(cls, values: Mapping[str, Any]):  # type: ignore[override]
        raw = values.get("dimensions")
        if raw is None:
            return dict(values)

        # Allow short form: dimensions: {"industry": {"present": false}}
        normalized: Dict[DimensionName, Any] = {}
        for key, dim in dict(raw).items():
            try:
                dim_name = DimensionName(key)
            except ValueError as exc:
                raise ValueError(f"Unknown dimension: {key}") from exc

            if dim is None:
                dim = {}
            if isinstance(dim, dict) and "name" not in dim:
                dim = {**dim, "name": dim_name}

            normalized[dim_name] = dim

        values = dict(values)
        values["dimensions"] = normalized
        return values


class CompiledAgentSpec(BaseModel):
    """Result of compiling an AgentSpec into an executable configuration bundle."""

    agent_id: str
    agent_type: str
    version: str
    dimensions: Dict[DimensionName, DimensionSpec]

    @classmethod
    def from_agent_spec(
        cls,
        spec: AgentSpec,
        *,
        default_null_dimensions: Optional[list[DimensionName]] = None,
    ) -> "CompiledAgentSpec":
        """Fill missing optional dimensions with explicit nulls."""

        if default_null_dimensions is None:
            default_null_dimensions = [
                DimensionName.INDUSTRY,
                DimensionName.TEAM,
                DimensionName.UI,
                DimensionName.LOCALIZATION,
            ]

        dims = dict(spec.dimensions)
        for dim_name in default_null_dimensions:
            if dim_name not in dims:
                dims[dim_name] = DimensionSpec(name=dim_name, present=False, config={})

        return cls(agent_id=spec.agent_id, agent_type=spec.agent_type, version=spec.version, dimensions=dims)
