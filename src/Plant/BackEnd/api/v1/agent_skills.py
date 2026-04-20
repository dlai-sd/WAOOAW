"""Agent-Skill relationship endpoints.

PLANT-SKILLS-1 E1-S2

GET    /agents/{agent_id}/skills              — list skills attached to an agent
POST   /agents/{agent_id}/skills              — attach a skill to an agent
DELETE /agents/{agent_id}/skills/{skill_id}   — detach a skill from an agent
PATCH  /skills/{skill_id}/goal-schema         — update skill goal_schema (drives CP dynamic form)
GET    /skills/{skill_id}                     — get skill including goal_schema
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import hired_agents_simple
from core.database import get_db, get_read_db_session
from core.routing import waooaw_router
from models.agent import Agent
from models.agent_skill import AgentSkillModel
from models.agent_catalog import AgentCatalogReleaseModel
from models.skill import Skill
from models.skill_config import SkillConfigModel
from agent_mold.registry import skill_registry

router = waooaw_router(prefix="/agents", tags=["agent-skills"])
skills_router = waooaw_router(prefix="/skills", tags=["skills"])
hired_agent_skills_router = waooaw_router(prefix="/hired-agents", tags=["hired-agent-skills"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_uuid(value: str) -> uuid.UUID:
    """Parse a string to UUID; raises 422 if invalid."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail=f"Invalid UUID: {value}")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AgentSkillResponse(BaseModel):
    id: str
    agent_id: str
    skill_id: str
    is_primary: bool
    ordinal: int
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    goal_schema: Optional[dict] = None   # from Skill.goal_schema — drives FE form fields
    goal_config: Optional[dict] = None   # from AgentSkillModel.goal_config — customer's saved values

    class Config:
        from_attributes = True


class AttachSkillRequest(BaseModel):
    skill_id: str
    is_primary: bool = False
    ordinal: int = 0


class GoalSchemaUpdateRequest(BaseModel):
    goal_schema: dict


class GoalConfigUpdateRequest(BaseModel):
    goal_config: dict


class SkillResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None
    goal_schema: Optional[dict] = None

    class Config:
        from_attributes = True


class RuntimeSkillResponse(BaseModel):
    skill_id: str
    name: str
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    platform_fields: dict[str, Any] = {}
    customer_fields: dict[str, Any] = {}
    goal_schema: Optional[dict] = None
    goal_config: Optional[dict] = None
    status: str = "active"


def _skill_filters(skill_id: str) -> list[Any]:
    clauses: list[Any] = [Skill.external_id == skill_id]
    try:
        clauses.append(Skill.id == _to_uuid(skill_id))
    except HTTPException:
        pass
    return clauses


async def _resolve_agent_uuid(agent_id: str, db: AsyncSession) -> uuid.UUID:
    try:
        return _to_uuid(agent_id)
    except HTTPException:
        pass

    result = await db.execute(select(Agent.id).where(Agent.external_id == agent_id))
    resolved = result.scalar_one_or_none()
    if resolved is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return resolved


def _runtime_goal_config(
    *,
    link_goal_config: dict | None,
    customer_fields: dict[str, Any] | None,
) -> dict | None:
    if link_goal_config is not None:
        return link_goal_config
    if customer_fields:
        return customer_fields
    return None


def build_runtime_skill_response(
    *,
    skill: Skill,
    skill_config: SkillConfigModel | None,
    goal_config: dict | None,
    status: str = "active",
) -> RuntimeSkillResponse:
    customer_fields = dict(getattr(skill_config, "customer_fields", {}) or {})
    platform_fields = dict(getattr(skill_config, "pp_locked_fields", {}) or {})
    return RuntimeSkillResponse(
        skill_id=str(skill.external_id or skill.id),
        name=skill.name,
        display_name=skill.name,
        description=skill.description,
        category=skill.category,
        platform_fields=platform_fields,
        customer_fields=customer_fields,
        goal_schema=skill.goal_schema,
        goal_config=_runtime_goal_config(
            link_goal_config=goal_config,
            customer_fields=customer_fields,
        ),
        status=status,
    )


async def get_runtime_skill_response_for_hire(
    *,
    hired_instance_id: str,
    skill_id: str,
    db: AsyncSession,
) -> RuntimeSkillResponse:
    record = await hired_agents_simple._get_record_by_id(
        hired_instance_id=hired_instance_id,
        db=db,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    agent_uuid = await _resolve_agent_uuid(record.agent_id, db)
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == agent_uuid)
        .where(or_(*_skill_filters(skill_id)))
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not attached to this hired agent")

    config_result = await db.execute(
        select(SkillConfigModel).where(
            SkillConfigModel.hired_instance_id == hired_instance_id,
            SkillConfigModel.skill_id == skill_id,
        )
    )
    skill_config = config_result.scalar_one_or_none()

    return build_runtime_skill_response(
        skill=row.Skill,
        skill_config=skill_config,
        goal_config=row.AgentSkillModel.goal_config,
    )


# ── Agent-Skill endpoints ─────────────────────────────────────────────────────

@router.get("/{agent_id}/skills", response_model=List[AgentSkillResponse])
async def list_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # read replica — never primary on GETs
) -> List[AgentSkillResponse]:
    """List all skills attached to an agent, ordered by ordinal.

    Primary path: look up agent in base_entity by UUID or external_id then return
    linked agent_skills rows.

    Catalog fallback: if the agent exists only in agent_catalog_releases (e.g. DMA
    agents seeded without entity rows), derive the skill list from the in-memory
    skill_registry using the visible_skills config on the AgentSpec.
    """
    try:
        agent_uuid = await _resolve_agent_uuid(agent_id, db)
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        # Entity row absent — try catalog fallback.
        return await _catalog_skills_fallback(agent_id=agent_id, db=db)

    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == agent_uuid)
        .order_by(AgentSkillModel.ordinal)
    )
    rows = result.all()
    if rows:
        return [
            AgentSkillResponse(
                id=row.AgentSkillModel.id,
                agent_id=str(row.AgentSkillModel.agent_id),
                skill_id=str(row.AgentSkillModel.skill_id),
                is_primary=row.AgentSkillModel.is_primary,
                ordinal=row.AgentSkillModel.ordinal,
                skill_name=row.Skill.name,
                skill_category=row.Skill.category,
                goal_schema=row.Skill.goal_schema,
                goal_config=row.AgentSkillModel.goal_config,
            )
            for row in rows
        ]
    # Agent entity row exists but has no linked skills — try catalog fallback.
    return await _catalog_skills_fallback(agent_id=agent_id, db=db)


async def _catalog_skills_fallback(
    *, agent_id: str, db: AsyncSession
) -> List[AgentSkillResponse]:
    """Return the visible skill list for an agent that exists only in agent_catalog_releases.

    Uses the in-memory skill_registry to build synthetic AgentSkillResponse rows,
    keyed by the visible_skills names defined in the AgentSpec for that agent_type_id.
    """
    # Look up the catalog entry to get agent_type_id.
    from agent_mold.registry import AgentSpecRegistry
    result = await db.execute(
        select(AgentCatalogReleaseModel.agent_type_id)
        .where(AgentCatalogReleaseModel.agent_id == agent_id)
        .where(AgentCatalogReleaseModel.approved_for_new_hire == True)  # noqa: E712
        .limit(1)
    )
    agent_type_id = result.scalar_one_or_none()
    if not agent_type_id:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

    # Resolve AgentSpec to get visible_skills list.
    spec = AgentSpecRegistry.instance().get_spec(agent_type_id)
    visible_names: list[str] = []
    if spec:
        skill_dim = (spec.dimensions or {}).get("skill") or {}
        config = skill_dim.get("config") if isinstance(skill_dim, dict) else {}
        visible_names = list(config.get("visible_skills") or []) if isinstance(config, dict) else []

    # Map visible skill names → registered skill entries.
    responses: list[AgentSkillResponse] = []
    for ordinal, name in enumerate(visible_names):
        name_lower = name.lower().replace(" ", "_")
        # Find a matching registry entry by skill_id suffix or display_name.
        entry = next(
            (
                e
                for e in skill_registry.list_all()
                if e.name.lower().replace(" ", "_") == name_lower
                or e.skill_id.lower().replace(".", "_").endswith(name_lower)
            ),
            None,
        )
        skill_id = entry.skill_id if entry else name_lower
        skill_name = entry.name if entry else name
        responses.append(
            AgentSkillResponse(
                id=f"{agent_id}.{skill_id}",
                agent_id=agent_id,
                skill_id=skill_id,
                is_primary=(ordinal == 0),
                ordinal=ordinal,
                skill_name=skill_name,
                skill_category=entry.category if entry else "technical",
                goal_schema=entry.goal_schema if entry else None,
                goal_config=None,
            )
        )
    return responses


@router.post("/{agent_id}/skills", response_model=AgentSkillResponse, status_code=201)
async def attach_skill(
    agent_id: str,
    body: AttachSkillRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentSkillResponse:
    """Attach a skill to an agent."""
    link = AgentSkillModel(
        id=str(uuid.uuid4()),
        agent_id=_to_uuid(agent_id),
        skill_id=_to_uuid(body.skill_id),
        is_primary=body.is_primary,
        ordinal=body.ordinal,
        created_at=datetime.now(timezone.utc),
    )
    db.add(link)
    try:
        await db.commit()
        await db.refresh(link)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Skill already attached to this agent")
    return AgentSkillResponse(
        id=link.id,
        agent_id=str(link.agent_id),
        skill_id=str(link.skill_id),
        is_primary=link.is_primary,
        ordinal=link.ordinal,
    )


@router.patch("/{agent_id}/skills/{skill_id}/goal-config", response_model=AgentSkillResponse)
async def update_goal_config(
    agent_id: str,
    skill_id: str,
    body: GoalConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentSkillResponse:
    """Persist the customer's goal configuration for a specific agent-skill link.

    CP-SKILLS-2 E1-S2 — stores body.goal_config into agent_skills.goal_config JSONB.
    Returns the full AgentSkillResponse (including goal_schema from Skill) so the
    FE can re-hydrate the form in one round-trip.
    """
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == _to_uuid(agent_id))
        .where(AgentSkillModel.skill_id == _to_uuid(skill_id))
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not attached to this agent")

    link, skill = row.AgentSkillModel, row.Skill
    link.goal_config = body.goal_config
    await db.commit()
    await db.refresh(link)

    return AgentSkillResponse(
        id=link.id,
        agent_id=str(link.agent_id),
        skill_id=str(link.skill_id),
        is_primary=link.is_primary,
        ordinal=link.ordinal,
        skill_name=skill.name,
        skill_category=skill.category,
        goal_schema=skill.goal_schema,
        goal_config=link.goal_config,
    )


@router.delete("/{agent_id}/skills/{skill_id}", status_code=204)
async def detach_skill(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Detach a skill from an agent."""
    result = await db.execute(
        delete(AgentSkillModel)
        .where(AgentSkillModel.agent_id == _to_uuid(agent_id))
        .where(AgentSkillModel.skill_id == _to_uuid(skill_id))
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Skill not attached to this agent")


# ── Skill endpoints ───────────────────────────────────────────────────────────

@skills_router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # read replica
) -> SkillResponse:
    """Get a skill by ID, including its goal_schema."""
    result = await db.execute(select(Skill).where(Skill.id == _to_uuid(skill_id)))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillResponse(
        id=str(skill.id),
        name=skill.name,
        category=skill.category,
        description=skill.description,
        goal_schema=skill.goal_schema,
    )


@skills_router.patch("/{skill_id}/goal-schema", response_model=dict)
async def update_goal_schema(
    skill_id: str,
    body: GoalSchemaUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update the goal_schema for a skill. Drives CP FrontEnd dynamic goal config form."""
    result = await db.execute(select(Skill).where(Skill.id == _to_uuid(skill_id)))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.goal_schema = body.goal_schema
    await db.commit()
    return {"skill_id": skill_id, "goal_schema": skill.goal_schema}


@hired_agent_skills_router.get("/{hired_instance_id}/skills", response_model=List[RuntimeSkillResponse])
async def list_hired_agent_skills(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[RuntimeSkillResponse]:
    record = await hired_agents_simple._get_record_by_id(
        hired_instance_id=hired_instance_id,
        db=db,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    agent_uuid = await _resolve_agent_uuid(record.agent_id, db)
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == agent_uuid)
        .order_by(AgentSkillModel.ordinal)
    )
    rows = result.all()

    config_result = await db.execute(
        select(SkillConfigModel).where(SkillConfigModel.hired_instance_id == hired_instance_id)
    )
    configs = {
        str(config.skill_id): config
        for config in config_result.scalars().all()
    }

    return [
        build_runtime_skill_response(
            skill=row.Skill,
            skill_config=configs.get(str(row.Skill.external_id or row.Skill.id)),
            goal_config=row.AgentSkillModel.goal_config,
        )
        for row in rows
    ]