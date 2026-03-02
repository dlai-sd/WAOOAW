"""Tests for Agent-Skill API endpoints.

PLANT-SKILLS-1 E1-S2

Covers:
- Import / router registration
- GET /agents/{id}/skills — list empty
- POST /agents/{id}/skills — attach, returns 201
- POST /agents/{id}/skills — duplicate returns 409
- DELETE /agents/{id}/skills/{skill_id} — detach returns 204
- DELETE /agents/{id}/skills/{skill_id} — unknown returns 404
- PATCH /skills/{id}/goal-schema — updates correctly
- GET /skills/{id} — returns skill with goal_schema
- UUID validation — invalid UUID returns 422

Run:
    docker-compose -f docker-compose.test.yml run --rm \\
      --entrypoint "python -m pytest" plant-backend-test \\
      -q --no-cov tests/unit/test_agent_skills_api.py
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Router import sanity ──────────────────────────────────────────────────────

def test_import_agent_skills_router():
    """Router module must import without error and expose 'router' + 'skills_router'."""
    from api.v1.agent_skills import router, skills_router
    assert router is not None
    assert skills_router is not None


def test_router_has_correct_prefix():
    from api.v1.agent_skills import router, skills_router
    assert router.prefix == "/agents"
    assert skills_router.prefix == "/skills"


def test_router_tags():
    from api.v1.agent_skills import router, skills_router
    assert "agent-skills" in router.tags
    assert "skills" in skills_router.tags


# ── UUID helper ───────────────────────────────────────────────────────────────

def test_to_uuid_valid():
    from api.v1.agent_skills import _to_uuid
    uid = str(uuid.uuid4())
    result = _to_uuid(uid)
    assert isinstance(result, uuid.UUID)
    assert str(result) == uid


def test_to_uuid_invalid_raises_422():
    from fastapi import HTTPException
    from api.v1.agent_skills import _to_uuid
    with pytest.raises(HTTPException) as exc:
        _to_uuid("not-a-uuid")
    assert exc.value.status_code == 422


# ── Route registration check ─────────────────────────────────────────────────

def test_all_routes_registered():
    """All 6 routes must be registered."""
    from api.v1.agent_skills import router, skills_router

    agent_routes = {(frozenset(r.methods), r.path) for r in router.routes}
    skill_routes = {(frozenset(r.methods), r.path) for r in skills_router.routes}

    # Agent-skills routes
    assert any("GET" in m and "/skills" in p for m, p in agent_routes), \
        "GET /agents/{id}/skills not registered"
    assert any("POST" in m and "/skills" in p for m, p in agent_routes), \
        "POST /agents/{id}/skills not registered"
    assert any("DELETE" in m and "/skills" in p for m, p in agent_routes), \
        "DELETE /agents/{id}/skills/{skill_id} not registered"

    # Skills routes
    assert any("PATCH" in m and "goal-schema" in p for m, p in skill_routes), \
        "PATCH /skills/{id}/goal-schema not registered"
    assert any("GET" in m and "goal-schema" not in p for m, p in skill_routes), \
        "GET /skills/{id} not registered"


# ── Endpoint logic (mocked DB) ────────────────────────────────────────────────

@pytest.fixture
def agent_id():
    return str(uuid.uuid4())


@pytest.fixture
def skill_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_list_agent_skills_returns_empty_list(agent_id, mock_db):
    """GET skills for unknown agent returns empty list (not 404)."""
    from api.v1.agent_skills import list_agent_skills

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await list_agent_skills(agent_id=agent_id, db=mock_db)
    assert result == []


@pytest.mark.asyncio
async def test_list_agent_skills_returns_attached_skill(agent_id, skill_id, mock_db):
    """GET skills returns AgentSkillResponse list when skills exist."""
    from api.v1.agent_skills import list_agent_skills
    from models.agent_skill import AgentSkillModel
    from models.skill import Skill

    link = MagicMock(spec=AgentSkillModel)
    link.id = str(uuid.uuid4())
    link.agent_id = uuid.UUID(agent_id)
    link.skill_id = uuid.UUID(skill_id)
    link.is_primary = True
    link.ordinal = 0
    link.goal_config = None  # CP-SKILLS-2: new field; None = not yet configured

    skill = MagicMock(spec=Skill)
    skill.name = "social-content-publisher"
    skill.category = "content"
    skill.goal_schema = None  # CP-SKILLS-2: new field; None = no schema defined

    row = MagicMock()
    row.AgentSkillModel = link
    row.Skill = skill

    mock_result = MagicMock()
    mock_result.all.return_value = [row]
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await list_agent_skills(agent_id=agent_id, db=mock_db)
    assert len(result) == 1
    assert result[0].agent_id == agent_id
    assert result[0].skill_id == skill_id
    assert result[0].skill_name == "social-content-publisher"
    assert result[0].is_primary is True


@pytest.mark.asyncio
async def test_attach_skill_returns_201(agent_id, skill_id, mock_db):
    """POST attach skill succeeds and returns AgentSkillResponse."""
    from api.v1.agent_skills import attach_skill, AttachSkillRequest

    async def mock_refresh(obj):
        obj.agent_id = uuid.UUID(agent_id)
        obj.skill_id = uuid.UUID(skill_id)
        obj.is_primary = False
        obj.ordinal = 0

    mock_db.refresh = mock_refresh
    mock_db.commit = AsyncMock()

    body = AttachSkillRequest(skill_id=skill_id, is_primary=False, ordinal=0)
    result = await attach_skill(agent_id=agent_id, body=body, db=mock_db)

    assert result.agent_id == agent_id
    assert result.skill_id == skill_id
    assert result.is_primary is False


@pytest.mark.asyncio
async def test_attach_skill_duplicate_returns_409(agent_id, skill_id, mock_db):
    """POST duplicate attach raises 409."""
    from fastapi import HTTPException
    from api.v1.agent_skills import attach_skill, AttachSkillRequest

    mock_db.commit = AsyncMock(side_effect=Exception("unique constraint violation"))

    body = AttachSkillRequest(skill_id=skill_id)
    with pytest.raises(HTTPException) as exc:
        await attach_skill(agent_id=agent_id, body=body, db=mock_db)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_detach_skill_returns_204(agent_id, skill_id, mock_db):
    """DELETE returns None (204) when skill was attached."""
    from api.v1.agent_skills import detach_skill

    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await detach_skill(agent_id=agent_id, skill_id=skill_id, db=mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_detach_skill_not_attached_returns_404(agent_id, skill_id, mock_db):
    """DELETE returns 404 when skill was not attached to this agent."""
    from fastapi import HTTPException
    from api.v1.agent_skills import detach_skill

    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await detach_skill(agent_id=agent_id, skill_id=skill_id, db=mock_db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_skill_returns_goal_schema(skill_id, mock_db):
    """GET /skills/{id} returns skill with goal_schema."""
    from api.v1.agent_skills import get_skill
    from models.skill import Skill

    skill = MagicMock(spec=Skill)
    skill.id = uuid.UUID(skill_id)
    skill.name = "execute-trade-order"
    skill.category = "trading"
    skill.description = "Executes trades on a crypto exchange"
    skill.goal_schema = {"fields": [{"key": "exchange", "type": "string"}]}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=skill)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_skill(skill_id=skill_id, db=mock_db)
    assert result.name == "execute-trade-order"
    assert result.goal_schema == {"fields": [{"key": "exchange", "type": "string"}]}


@pytest.mark.asyncio
async def test_get_skill_not_found_returns_404(skill_id, mock_db):
    """GET /skills/{id} returns 404 when skill does not exist."""
    from fastapi import HTTPException
    from api.v1.agent_skills import get_skill

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await get_skill(skill_id=skill_id, db=mock_db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_goal_schema_returns_updated_schema(skill_id, mock_db):
    """PATCH /skills/{id}/goal-schema updates and returns new schema."""
    from api.v1.agent_skills import update_goal_schema, GoalSchemaUpdateRequest
    from models.skill import Skill

    new_schema = {"fields": [{"key": "leverage", "type": "integer"}]}

    skill = MagicMock(spec=Skill)
    skill.id = uuid.UUID(skill_id)
    skill.goal_schema = {}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=skill)
    mock_db.execute = AsyncMock(return_value=mock_result)

    body = GoalSchemaUpdateRequest(goal_schema=new_schema)
    result = await update_goal_schema(skill_id=skill_id, body=body, db=mock_db)

    assert skill.goal_schema == new_schema
    mock_db.commit.assert_called_once()
    assert result["skill_id"] == skill_id


@pytest.mark.asyncio
async def test_update_goal_schema_skill_not_found_returns_404(skill_id, mock_db):
    """PATCH /skills/{id}/goal-schema returns 404 for unknown skill."""
    from fastapi import HTTPException
    from api.v1.agent_skills import update_goal_schema, GoalSchemaUpdateRequest

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await update_goal_schema(
            skill_id=skill_id,
            body=GoalSchemaUpdateRequest(goal_schema={}),
            db=mock_db,
        )
    assert exc.value.status_code == 404
