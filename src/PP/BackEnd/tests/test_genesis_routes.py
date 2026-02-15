from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt

import pytest

from core.config import settings


def _mint_admin_token(monkeypatch) -> str:
    import time

    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _admin_headers(monkeypatch) -> dict:
    token = _mint_admin_token(monkeypatch)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit
async def test_create_skill_success(app, client, monkeypatch):
    from clients.plant_client import get_plant_client

    fake_skill = SimpleNamespace(
        id="skill-1",
        name="Python 3.11",
        description="Modern Python",
        category="technical",
        status="pending_certification",
        created_at="2026-01-01T00:00:00Z",
    )
    plant = SimpleNamespace(create_skill=AsyncMock(return_value=fake_skill))

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.post(
            "/api/pp/genesis/skills",
            json={
                "name": "Python 3.11",
                "description": "Modern Python",
                "category": "technical",
                "governance_agent_id": "genesis",
            },
            headers=_admin_headers(monkeypatch),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "skill-1"
        assert data["status"] == "pending_certification"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_create_skill_duplicate_maps_to_409(app, client, monkeypatch):
    from clients.plant_client import DuplicateEntityError, get_plant_client

    plant = SimpleNamespace(create_skill=AsyncMock(side_effect=DuplicateEntityError("dupe")))

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.post(
            "/api/pp/genesis/skills",
            json={"name": "X", "description": "Y", "category": "technical"},
            headers=_admin_headers(monkeypatch),
        )
        assert resp.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_list_skills_success(app, client, monkeypatch):
    from clients.plant_client import get_plant_client

    plant = SimpleNamespace(
        list_skills=AsyncMock(
            return_value=[
                SimpleNamespace(
                    id="skill-1",
                    name="Python",
                    description="desc",
                    category="technical",
                    status="certified",
                    created_at="2026-01-01T00:00:00Z",
                )
            ]
        )
    )

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get(
            "/api/pp/genesis/skills?category=technical",
            headers=_admin_headers(monkeypatch),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "skill-1"
        assert data[0]["category"] == "technical"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_get_skill_success(app, client, monkeypatch):
    from clients.plant_client import get_plant_client

    fake_skill = SimpleNamespace(
        id="skill-1",
        name="Python",
        description="desc",
        category="technical",
        entity_type="skill",
        status="certified",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        l0_compliance_status={},
    )
    plant = SimpleNamespace(get_skill=AsyncMock(return_value=fake_skill))

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.get(
            "/api/pp/genesis/skills/skill-1",
            headers=_admin_headers(monkeypatch),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "skill-1"
        assert data["l0_compliance_status"] == {}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_certify_skill_success(app, client, monkeypatch):
    from clients.plant_client import get_plant_client

    plant = SimpleNamespace(
        certify_skill=AsyncMock(
            return_value=SimpleNamespace(id="skill-1", name="Python", status="certified")
        )
    )

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.post(
            "/api/pp/genesis/skills/skill-1/certify",
            json={},
            headers=_admin_headers(monkeypatch),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "certified"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_job_role_endpoints_smoke(app, client, monkeypatch):
    from clients.plant_client import get_plant_client

    role = SimpleNamespace(
        id="role-1",
        name="Content Writer",
        description="writes",
        required_skills=["skill-1"],
        seniority_level="mid",
        entity_type="job_role",
        status="pending_certification",
        created_at="2026-01-01T00:00:00Z",
    )

    plant = SimpleNamespace(
        create_job_role=AsyncMock(return_value=role),
        list_job_roles=AsyncMock(return_value=[role]),
        get_job_role=AsyncMock(return_value=role),
        certify_job_role=AsyncMock(return_value=SimpleNamespace(id="role-1", name="Content Writer", status="certified")),
    )

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        headers = _admin_headers(monkeypatch)
        resp = await client.post(
            "/api/pp/genesis/job-roles",
            json={
                "name": "Content Writer",
                "description": "writes",
                "required_skills": ["skill-1"],
                "seniority_level": "mid",
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp = await client.get("/api/pp/genesis/job-roles", headers=headers)
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "role-1"

        resp = await client.get("/api/pp/genesis/job-roles/role-1", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == "role-1"

        resp = await client.post(
            "/api/pp/genesis/job-roles/role-1/certify",
            json={},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "certified"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
async def test_create_job_role_duplicate_maps_to_409(app, client, monkeypatch):
    from clients.plant_client import DuplicateEntityError, get_plant_client

    plant = SimpleNamespace(
        create_job_role=AsyncMock(side_effect=DuplicateEntityError("Duplicate"))
    )

    app.dependency_overrides[get_plant_client] = lambda: plant
    try:
        resp = await client.post(
            "/api/pp/genesis/job-roles",
            json={
                "name": "Content Writer",
                "description": "writes",
                "required_skills": ["skill-1"],
                "seniority_level": "mid",
            },
            headers=_admin_headers(monkeypatch),
        )

        assert resp.status_code == 409
        data = resp.json()
        assert data["status"] == 409
        assert data["title"] == "Conflict"
        assert "Duplicate" in data["detail"]
    finally:
        app.dependency_overrides.clear()
