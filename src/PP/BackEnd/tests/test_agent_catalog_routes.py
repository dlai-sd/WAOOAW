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
async def test_list_catalog_releases_forwards_to_plant(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    seen = {}

    async def _fake_list(self, correlation_id=None, auth_header=None):
        seen["correlation_id"] = correlation_id
        seen["auth_header"] = auth_header
        return [{"release_id": "CAR-1", "id": "AGT-MKT-001", "public_name": "Digital Marketing Agent"}]

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.list_catalog_releases",
        _fake_list,
    )

    res = await client.get(
        "/api/pp/agent-catalog",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-cat-1"},
    )
    assert res.status_code == 200
    assert res.json()[0]["release_id"] == "CAR-1"
    assert seen["correlation_id"] == "cid-cat-1"
    assert seen["auth_header"].startswith("Bearer ")


@pytest.mark.unit
async def test_upsert_catalog_release_calls_audit_log(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []

    async def _fake_upsert(self, agent_id, payload, correlation_id=None, auth_header=None):
        return {"release_id": "CAR-2", "id": agent_id, **payload}

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.upsert_catalog_release",
        _fake_upsert,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    payload = {
        "public_name": "Digital Marketing Agent",
        "monthly_price_inr": 12000,
        "trial_days": 7,
        "allowed_durations": ["monthly", "quarterly"],
        "supported_channels": ["youtube"],
        "approval_mode": "manual_review",
        "external_catalog_version": "v1",
        "agent_type_id": "marketing.digital_marketing.v1",
    }

    res = await client.put(
        "/api/pp/agent-catalog/AGT-MKT-001/release",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert res.status_code == 200
    assert res.json()["id"] == "AGT-MKT-001"
    assert any(call["action"] == "catalog_release_updated" for call in audit_calls)


@pytest.mark.unit
async def test_approve_catalog_release_calls_audit_log(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []

    async def _fake_approve(self, agent_id, correlation_id=None, auth_header=None):
        return {"release_id": "CAR-3", "id": agent_id, "lifecycle_state": "live_on_cp"}

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.approve_catalog_release",
        _fake_approve,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    res = await client.post(
        "/api/pp/agent-catalog/AGT-MKT-001/approve",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-cat-2"},
    )
    assert res.status_code == 200
    assert res.json()["lifecycle_state"] == "live_on_cp"
    assert any(call["action"] == "catalog_release_approved" for call in audit_calls)


@pytest.mark.unit
async def test_retire_catalog_release_calls_audit_log(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []

    async def _fake_retire(self, release_id, correlation_id=None, auth_header=None):
        return {"release_id": release_id, "lifecycle_state": "retired_from_catalog"}

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.retire_catalog_release",
        _fake_retire,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    res = await client.post(
        "/api/pp/agent-catalog/releases/CAR-3/retire",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["lifecycle_state"] == "retired_from_catalog"
    assert any(call["action"] == "catalog_release_retired" for call in audit_calls)