from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest


def _json_response(status_code: int, payload: Any) -> httpx.Response:
    req = httpx.Request("GET", "http://plant")
    return httpx.Response(status_code, json=payload, request=req)


@pytest.mark.unit
def test_parse_error_fallback_non_json():
    from clients.plant_client import PlantAPIClient, PlantAPIError

    client = PlantAPIClient(base_url="http://plant")
    req = httpx.Request("GET", "http://plant")
    resp = httpx.Response(500, content=b"not-json", request=req)
    exc = client._parse_error(resp)
    assert isinstance(exc, PlantAPIError)


@pytest.mark.unit
def test_parse_error_maps_status_codes_and_types():
    from clients.plant_client import (
        ConstitutionalAlignmentError,
        DuplicateEntityError,
        EntityNotFoundError,
        PlantAPIClient,
        ValidationError,
    )

    client = PlantAPIClient(base_url="http://plant")

    exc = client._parse_error(_json_response(404, {"detail": "missing"}))
    assert isinstance(exc, EntityNotFoundError)

    exc = client._parse_error(_json_response(409, {"detail": "dupe"}))
    assert isinstance(exc, DuplicateEntityError)

    exc = client._parse_error(
        _json_response(
            422,
            {
                "type": "constitutional_violation",
                "detail": "bad",
                "violations": ["L0-01"],
            },
        )
    )
    assert isinstance(exc, ConstitutionalAlignmentError)

    exc = client._parse_error(
        _json_response(
            422,
            {"type": "validation_error", "detail": "bad", "violations": ["field"]},
        )
    )
    assert isinstance(exc, ValidationError)


@pytest.mark.unit
async def test_client_methods_success_paths(monkeypatch):
    from clients.plant_client import PlantAPIClient, JobRoleCreate, AgentCreate, SkillCreate

    client = PlantAPIClient(base_url="http://plant")

    async def fake_request(
        method: str,
        path: str,
        json_data: Dict[str, Any] | None = None,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        if method == "POST" and path == "/api/v1/genesis/skills":
            return _json_response(201, {"id": "s1", **(json_data or {})})
        if method == "GET" and path == "/api/v1/genesis/skills":
            return _json_response(200, [{"id": "s1", "name": "n", "description": "d", "category": "technical"}])
        if method == "GET" and path.startswith("/api/v1/genesis/skills/") and not path.endswith("/certify"):
            return _json_response(200, {"id": "s1", "name": "n", "description": "d", "category": "technical"})
        if method == "POST" and path.endswith("/certify") and "/genesis/skills/" in path:
            return _json_response(
                200,
                {
                    "id": "s1",
                    "name": "n",
                    "description": "d",
                    "category": "technical",
                    "status": "certified",
                },
            )

        if method == "POST" and path == "/api/v1/genesis/job-roles":
            return _json_response(201, {"id": "r1", **(json_data or {})})
        if method == "GET" and path == "/api/v1/genesis/job-roles":
            return _json_response(200, [{"id": "r1", "name": "role", "description": "d"}])
        if method == "GET" and path.startswith("/api/v1/genesis/job-roles/") and not path.endswith("/certify"):
            return _json_response(200, {"id": "r1", "name": "role", "description": "d"})
        if method == "POST" and path.endswith("/certify") and "/genesis/job-roles/" in path:
            return _json_response(200, {"id": "r1", "name": "role", "description": "d", "status": "certified"})

        if method == "POST" and path == "/api/v1/agents":
            return _json_response(201, {"id": "a1", **(json_data or {})})
        if method == "GET" and path == "/api/v1/agents":
            return _json_response(200, [{"id": "a1", "name": "agent", "job_role_id": "r1", "industry": "marketing"}])
        if method == "GET" and path.startswith("/api/v1/agents/") and "/assign-team" not in path:
            return _json_response(200, {"id": "a1", "name": "agent", "job_role_id": "r1", "industry": "marketing"})
        if method == "POST" and path.endswith("/assign-team"):
            return _json_response(200, {"id": "a1", "name": "agent", "team_id": "t1"})

        return _json_response(500, {"title": "oops", "detail": "nope"})

    monkeypatch.setattr(client, "_request", fake_request)

    # Skills
    skill = await client.create_skill(SkillCreate(name="n", description="d", category="technical"))
    assert skill.id == "s1"

    skills = await client.list_skills(category="technical")
    assert skills[0].id == "s1"

    skill = await client.get_skill("s1")
    assert skill.id == "s1"

    skill = await client.certify_skill("s1", {})
    assert skill.id == "s1"

    # Job roles
    role = await client.create_job_role(JobRoleCreate(name="role", description="d", required_skills=[]))
    assert role.id == "r1"

    roles = await client.list_job_roles()
    assert roles[0].id == "r1"

    role = await client.get_job_role("r1")
    assert role.id == "r1"

    role = await client.certify_job_role("r1", {})
    assert role.id == "r1"

    # Agents
    agent = await client.create_agent(AgentCreate(name="agent", job_role_id="r1", industry="marketing"))
    assert agent.id == "a1"

    agents = await client.list_agents(industry="marketing", status="active")
    assert agents[0].id == "a1"

    agent = await client.get_agent("a1")
    assert agent.id == "a1"

    agent = await client.assign_agent_to_team("a1", "t1")
    assert agent.team_id == "t1"

    await client.close()


@pytest.mark.unit
async def test_request_sets_correlation_id_header(monkeypatch):
    from clients.plant_client import PlantAPIClient

    client = PlantAPIClient(base_url="http://plant")
    captured: Dict[str, Any] = {}

    async def fake_http_request(*, method: str, url: str, json=None, params=None, headers=None):
        captured["headers"] = headers
        req = httpx.Request(method, url)
        return httpx.Response(200, json={}, request=req)

    monkeypatch.setattr(client.client, "request", fake_http_request)

    resp = await client._request(method="GET", path="/api/v1/ping")
    assert resp.status_code == 200
    assert captured["headers"]["X-Correlation-ID"]

    await client.close()
