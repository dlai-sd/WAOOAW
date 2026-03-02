"""Tests for agent_skills.py endpoints.

CP-SKILLS-2 E1-S2 — tests the new PATCH goal-config route and the updated
GET list response (which now includes goal_schema + goal_config fields).

These tests mock the DB session so they run without a live Postgres instance.
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from fastapi import FastAPI

from core.database import get_db, get_read_db_session


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_skill(skill_id: str) -> MagicMock:
    skill = MagicMock()
    skill.id = uuid.UUID(skill_id)
    skill.name = "Content Writer"
    skill.category = "marketing"
    skill.description = "Writes content"
    skill.goal_schema = {"type": "object", "properties": {"topic": {"type": "string"}}}
    return skill


def _make_link(agent_id: str, skill_id: str, goal_config: dict | None = None) -> MagicMock:
    link = MagicMock()
    link.id = str(uuid.uuid4())
    link.agent_id = uuid.UUID(agent_id)
    link.skill_id = uuid.UUID(skill_id)
    link.is_primary = True
    link.ordinal = 0
    link.goal_config = goal_config
    return link


def _row(link, skill) -> MagicMock:
    row = MagicMock()
    row.AgentSkillModel = link
    row.Skill = skill
    return row


# ── Fixtures ──────────────────────────────────────────────────────────────────

_AGENT_ID = str(uuid.uuid4())
_SKILL_ID = str(uuid.uuid4())


@pytest.fixture
def mock_read_session() -> AsyncMock:
    """Minimal async mock for get_read_db_session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_write_session() -> AsyncMock:
    """Minimal async mock for get_db (write session)."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
async def client(mock_read_session, mock_write_session) -> AsyncGenerator:
    """Async test client with DB dependencies overridden."""
    from fastapi import FastAPI
    from api.v1.agent_skills import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _override_read():
        yield mock_read_session

    async def _override_write():
        yield mock_write_session

    app.dependency_overrides[get_read_db_session] = _override_read
    app.dependency_overrides[get_db] = _override_write

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── GET /agents/{agent_id}/skills ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_agent_skills_includes_goal_fields(client, mock_read_session):
    """GET list response must include goal_schema and goal_config fields."""
    skill = _make_skill(_SKILL_ID)
    link = _make_link(_AGENT_ID, _SKILL_ID, goal_config={"topic": "AI trends"})
    row = _row(link, skill)

    execute_result = MagicMock()
    execute_result.all.return_value = [row]
    mock_read_session.execute = AsyncMock(return_value=execute_result)

    resp = await client.get(f"/api/v1/agents/{_AGENT_ID}/skills")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    item = data[0]
    assert item["skill_name"] == "Content Writer"
    assert item["goal_schema"] == skill.goal_schema
    assert item["goal_config"] == {"topic": "AI trends"}


@pytest.mark.asyncio
async def test_list_agent_skills_goal_config_none_when_not_set(client, mock_read_session):
    """goal_config should be null in response when not yet configured."""
    skill = _make_skill(_SKILL_ID)
    link = _make_link(_AGENT_ID, _SKILL_ID, goal_config=None)
    row = _row(link, skill)

    execute_result = MagicMock()
    execute_result.all.return_value = [row]
    mock_read_session.execute = AsyncMock(return_value=execute_result)

    resp = await client.get(f"/api/v1/agents/{_AGENT_ID}/skills")

    assert resp.status_code == 200
    assert resp.json()[0]["goal_config"] is None


# ── PATCH /agents/{agent_id}/skills/{skill_id}/goal-config ────────────────────

@pytest.mark.asyncio
async def test_patch_goal_config_success(client, mock_write_session):
    """PATCH goal-config persists goal_config and returns full AgentSkillResponse."""
    skill = _make_skill(_SKILL_ID)
    link = _make_link(_AGENT_ID, _SKILL_ID, goal_config=None)

    # After save, link.goal_config is updated in place by the route
    async def _refresh(obj):
        obj.goal_config = {"topic": "new value"}

    mock_write_session.refresh = _refresh

    execute_result = MagicMock()
    execute_result.one_or_none.return_value = MagicMock(
        AgentSkillModel=link, Skill=skill
    )
    mock_write_session.execute = AsyncMock(return_value=execute_result)

    resp = await client.patch(
        f"/api/v1/agents/{_AGENT_ID}/skills/{_SKILL_ID}/goal-config",
        json={"goal_config": {"topic": "new value"}},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["goal_config"] == {"topic": "new value"}
    assert data["skill_name"] == "Content Writer"
    assert data["goal_schema"] == skill.goal_schema
    mock_write_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_goal_config_not_found(client, mock_write_session):
    """PATCH goal-config returns 404 when the skill is not attached to the agent."""
    execute_result = MagicMock()
    execute_result.one_or_none.return_value = None
    mock_write_session.execute = AsyncMock(return_value=execute_result)

    resp = await client.patch(
        f"/api/v1/agents/{_AGENT_ID}/skills/{_SKILL_ID}/goal-config",
        json={"goal_config": {"topic": "x"}},
    )

    assert resp.status_code == 404
    assert "not attached" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_patch_goal_config_invalid_agent_uuid(client):
    """PATCH with non-UUID agent_id returns 422."""
    resp = await client.patch(
        "/api/v1/agents/not-a-uuid/skills/also-not-uuid/goal-config",
        json={"goal_config": {}},
    )
    assert resp.status_code == 422
