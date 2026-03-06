"""Dimension registry + Skill registry.

Chunk A: minimal registry that can validate and compile an AgentSpec.
Skill registry: maps skill_id → SkillRegistryEntry for agent catalog discovery.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from agent_mold.contracts import BasicDimension, DimensionContract, DimensionContext, RuntimeBundle
from agent_mold.skills.playbook import SkillCategory
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


# ─── Skill Registry ──────────────────────────────────────────────────────────
# Maps skill_id → SkillRegistryEntry. Used by agent catalogs and CP BackEnd.
# To register a new skill: call skill_registry.register(SkillRegistryEntry(...))

class SkillRegistryEntry(BaseModel):
    """Descriptor for a registered skill — used by agent catalogs and CP BackEnd."""

    skill_id: str = Field(..., description="Stable unique identifier, e.g. 'content.creator.v1'")
    name: str = Field(..., description="Human-readable name")
    category: SkillCategory
    description: str
    version: str = "1.0.0"
    required_config_keys: List[str] = Field(
        default_factory=list,
        description="Config keys that must be present for the skill to function",
    )
    optional_config_keys: List[str] = Field(
        default_factory=list,
        description="Config keys that enhance behaviour when present",
    )


class SkillRegistry:
    """Maps skill_id → SkillRegistryEntry. Thread-safe for reads (register only at startup)."""

    def __init__(self) -> None:
        self._entries: Dict[str, SkillRegistryEntry] = {}

    def register(self, entry: SkillRegistryEntry) -> None:
        self._entries[entry.skill_id] = entry

    def get(self, skill_id: str) -> Optional[SkillRegistryEntry]:
        return self._entries.get(skill_id)

    def list_all(self) -> List[SkillRegistryEntry]:
        return list(self._entries.values())

    def is_registered(self, skill_id: str) -> bool:
        return skill_id in self._entries


# ── Default skill registry (populated at module import) ───────────────────────

skill_registry = SkillRegistry()

skill_registry.register(SkillRegistryEntry(
    skill_id="content.creator.v1",
    name="Content Creator",
    category=SkillCategory.CONTENT,
    description=(
        "Generates a full content calendar and platform-specific posts from a campaign brief. "
        "Supports Grok LLM (XAI_API_KEY) or deterministic mode. "
        "Outputs: DailyThemeList + ContentPosts + CostEstimate."
    ),
    version="1.0.0",
    required_config_keys=[],
    optional_config_keys=["executor_backend", "xai_api_key"],
))

skill_registry.register(SkillRegistryEntry(
    skill_id="content.publisher.v1",
    name="Content Publisher",
    category=SkillCategory.CONTENT,
    description=(
        "Publishes approved ContentPosts to registered destinations via the DestinationRegistry. "
        "Phase 1: simulated adapter. Phase 2: platform OAuth adapters (LinkedIn, Instagram, YouTube). "
        "Plug-and-play — new platform = new file + registry entry."
    ),
    version="1.0.0",
    required_config_keys=[],
    optional_config_keys=["destination_type", "credential_ref"],
))
