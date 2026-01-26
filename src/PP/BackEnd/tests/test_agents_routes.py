from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
async def test_agents_crud_and_assign_team(app, client):
    from clients.plant_client import get_plant_client

    agent = SimpleNamespace(
        id="agent-1",
        name="Agent One",
        description="desc",
        job_role_id="role-1",
        industry="marketing",
        status="inactive",
        team_id=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at=None,
        entity_type="agent",
        l0_compliance_status={},
    )

    plant = SimpleNamespace(
        create_agent=AsyncMock(return_value=agent),
        list_agents=AsyncMock(return_value=[agent]),
        get_agent=AsyncMock(return_value=agent),
        assign_agent_to_team=AsyncMock(return_value=SimpleNamespace(id="agent-1", name="Agent One", team_id="team-1")),
    )

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.post(
            "/api/pp/agents",
            json={
                "name": "Agent One",
                "description": "desc",
                "job_role_id": "role-1",
                "industry": "marketing",
                "governance_agent_id": "genesis",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "agent-1"

        resp = await client.get("/api/pp/agents?industry=marketing")
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "agent-1"

        resp = await client.get("/api/pp/agents/agent-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "agent-1"

        resp = await client.post("/api/pp/agents/agent-1/assign-team", json={"team_id": "team-1"})
        assert resp.status_code == 200
        assert resp.json()["team_id"] == "team-1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_update_agent_status_returns_501(client):
    resp = await client.patch("/api/pp/agents/agent-1/status", json={"status": "active"})
    assert resp.status_code == 501
