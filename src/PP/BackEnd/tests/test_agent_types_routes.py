from __future__ import annotations

import time

import jwt
import pytest

from core.config import settings


def _mint_admin_token() -> str:
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


@pytest.mark.unit
async def test_list_agent_types_requires_admin(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    res = await client.get("/api/pp/agent-types")
    assert res.status_code == 401


@pytest.mark.unit
async def test_list_agent_types_forwards_to_plant(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    seen = {}

    async def _fake_list(self, correlation_id=None, auth_header=None):
        seen["correlation_id"] = correlation_id
        seen["auth_header"] = auth_header
        return [
            {"agent_type_id": "marketing.healthcare.v1", "version": "1.0.0"},
            {"agent_type_id": "trading.delta_futures.v1", "version": "1.0.0"},
        ]

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.list_agent_type_definitions",
        _fake_list,
    )

    res = await client.get(
        "/api/pp/agent-types",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert seen["correlation_id"] == "cid-123"
    assert seen["auth_header"].startswith("Bearer ")


@pytest.mark.unit
async def test_publish_agent_type_rejects_invalid_schema(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()

    payload = {
        "agent_type_id": "marketing.healthcare.v1",
        "version": "1.0.0",
        "config_schema": {
            "fields": [
                {"key": "nickname", "label": "Nickname", "type": "nope", "required": True}
            ]
        },
        "goal_templates": [],
        "enforcement_defaults": {"approval_required": True, "deterministic": False},
    }

    res = await client.put(
        "/api/pp/agent-types/marketing.healthcare.v1",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert res.status_code == 422


@pytest.mark.unit
async def test_publish_agent_type_forwards_to_plant(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    seen = {}

    async def _fake_upsert(self, agent_type_id, payload, correlation_id=None, auth_header=None):
        seen["agent_type_id"] = agent_type_id
        seen["payload"] = payload
        seen["correlation_id"] = correlation_id
        seen["auth_header"] = auth_header
        return payload

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.upsert_agent_type_definition",
        _fake_upsert,
    )

    payload = {
        "agent_type_id": "marketing.healthcare.v1",
        "version": "1.0.9",
        "config_schema": {"fields": [{"key": "nickname", "label": "Nickname", "type": "text", "required": True}]},
        "goal_templates": [],
        "enforcement_defaults": {"approval_required": True, "deterministic": False},
    }

    res = await client.put(
        "/api/pp/agent-types/marketing.healthcare.v1",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-456"},
        json=payload,
    )
    assert res.status_code == 200
    assert seen["agent_type_id"] == "marketing.healthcare.v1"
    assert seen["correlation_id"] == "cid-456"
    assert seen["auth_header"].startswith("Bearer ")
    assert seen["payload"]["version"] == "1.0.9"
