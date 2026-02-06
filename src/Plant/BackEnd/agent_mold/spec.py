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

    @root_validator(skip_on_failure=True)
    def _validate_dimensions(cls, values: Dict[str, Any]):  # type: ignore[override]
        dimensions: Dict[DimensionName, DimensionSpec] = values.get("dimensions") or {}

        supported_versions: Dict[DimensionName, set[str]] = {
            DimensionName.SKILL: {"1.0"},
            DimensionName.INDUSTRY: {"1.0"},
            DimensionName.TEAM: {"1.0"},
            DimensionName.INTEGRATIONS: {"1.0"},
            DimensionName.UI: {"1.0"},
            DimensionName.LOCALIZATION: {"1.0"},
            DimensionName.TRIAL: {"1.0"},
            DimensionName.BUDGET: {"1.0"},
        }

        # Dimension-specific required config keys when present=true.
        required_keys: Dict[DimensionName, set[str]] = {
            DimensionName.SKILL: {"category"},
            DimensionName.INDUSTRY: {"industry"},
            DimensionName.TEAM: {"team_id"},
            DimensionName.INTEGRATIONS: {"providers"},
            DimensionName.UI: {"ui"},
            DimensionName.LOCALIZATION: {"language"},
            DimensionName.TRIAL: set(),
            DimensionName.BUDGET: set(),
        }

        for dim_name, dim_spec in dimensions.items():
            if dim_spec.name != dim_name:
                raise ValueError(
                    f"Dimension spec name mismatch for {dim_name.value}: got {dim_spec.name.value!r}"
                )

            supported = supported_versions.get(dim_name, {"1.0"})
            if dim_spec.version not in supported:
                raise ValueError(
                    f"Unsupported version {dim_spec.version!r} for dimension {dim_name.value}; supported={sorted(supported)}"
                )

            config = dim_spec.config or {}

            # Null dimensions must be explicit and safe: no hidden config payload.
            if dim_spec.present is False:
                if config:
                    raise ValueError(
                        f"Null dimension {dim_name.value} must not include config"
                    )
                continue

            # Present dimensions must not be partially configured.
            missing = sorted(required_keys.get(dim_name, set()) - set(config.keys()))
            if missing:
                raise ValueError(
                    f"Dimension {dim_name.value} is present but missing required config keys: {missing}"
                )

            if dim_name == DimensionName.SKILL:
                primary_playbook_id = config.get("primary_playbook_id")
                primary_skill = config.get("primary_skill")
                if not primary_playbook_id and not primary_skill:
                    raise ValueError(
                        "Dimension skill is present but missing a primary identifier: one of ['primary_playbook_id', 'primary_skill']"
                    )

                category = config.get("category")
                if not isinstance(category, str) or not category.strip():
                    raise ValueError("Dimension skill config['category'] must be a non-empty string")

                if "autopublish_allowed" in config and not isinstance(config.get("autopublish_allowed"), bool):
                    raise ValueError("Dimension skill config['autopublish_allowed'] must be a boolean")

            if dim_name == DimensionName.INDUSTRY:
                industry = config.get("industry")
                if not isinstance(industry, str) or not industry.strip():
                    raise ValueError("Dimension industry config['industry'] must be a non-empty string")

            if dim_name == DimensionName.UI:
                ui = config.get("ui")
                if not isinstance(ui, str) or not ui.strip():
                    raise ValueError("Dimension ui config['ui'] must be a non-empty string")

            if dim_name == DimensionName.LOCALIZATION:
                language = config.get("language")
                if not isinstance(language, str) or not language.strip():
                    raise ValueError("Dimension localization config['language'] must be a non-empty string")

            if dim_name == DimensionName.TEAM:
                team_id = config.get("team_id")
                if not isinstance(team_id, str) or not team_id.strip():
                    raise ValueError("Dimension team config['team_id'] must be a non-empty string")

            if dim_name == DimensionName.INTEGRATIONS:
                providers = config.get("providers")
                if not isinstance(providers, list) or not providers:
                    raise ValueError("Dimension integrations config['providers'] must be a non-empty list")

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
