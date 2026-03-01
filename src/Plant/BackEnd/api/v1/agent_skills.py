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
from typing import List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, get_read_db_session
from core.routing import waooaw_router
from models.agent_skill import AgentSkillModel
from models.skill import Skill

router = waooaw_router(prefix="/agents", tags=["agent-skills"])
skills_router = waooaw_router(prefix="/skills", tags=["skills"])


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

    class Config:
        from_attributes = True


class AttachSkillRequest(BaseModel):
    skill_id: str
    is_primary: bool = False
    ordinal: int = 0


class GoalSchemaUpdateRequest(BaseModel):
    goal_schema: dict


class SkillResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None
    goal_schema: Optional[dict] = None

    class Config:
        from_attributes = True


# ── Agent-Skill endpoints ─────────────────────────────────────────────────────

@router.get("/{agent_id}/skills", response_model=List[AgentSkillResponse])
async def list_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # read replica — never primary on GETs
) -> List[AgentSkillResponse]:
    """List all skills attached to an agent, ordered by ordinal."""
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == _to_uuid(agent_id))
        .order_by(AgentSkillModel.ordinal)
    )
    rows = result.all()
    return [
        AgentSkillResponse(
            id=row.AgentSkillModel.id,
            agent_id=str(row.AgentSkillModel.agent_id),
            skill_id=str(row.AgentSkillModel.skill_id),
            is_primary=row.AgentSkillModel.is_primary,
            ordinal=row.AgentSkillModel.ordinal,
            skill_name=row.Skill.name,
            skill_category=row.Skill.category,
        )
        for row in rows
    ]


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