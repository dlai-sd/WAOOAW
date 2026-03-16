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


def _draft_payload(status: str = "draft") -> dict:
    return {
        "draft_id": "AAD-1",
        "candidate_agent_type_id": "marketing.digital_marketing_agent",
        "candidate_agent_label": "Digital Marketing Agent",
        "contract_payload": {"identity": {"name": "DMA"}},
        "section_states": {"identity": "ready"},
        "constraint_policy": {"approval_required": True},
        "reviewer_comments": [],
        "status": status,
    }


@pytest.mark.unit
async def test_list_agent_authoring_drafts_requires_admin(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    response = await client.get("/api/pp/agent-authoring/drafts")
    assert response.status_code == 401


@pytest.mark.unit
async def test_list_agent_authoring_drafts_forwards_status_and_correlation(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    seen = {}

    async def _fake_list(self, status=None, correlation_id=None, auth_header=None):
        seen["status"] = status
        seen["correlation_id"] = correlation_id
        seen["auth_header"] = auth_header
        return [_draft_payload()]

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.list_agent_authoring_drafts",
        _fake_list,
    )

    response = await client.get(
        "/api/pp/agent-authoring/drafts?status=draft",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-201"},
    )

    assert response.status_code == 200
    assert response.json()[0]["draft_id"] == "AAD-1"
    assert seen["status"] == "draft"
    assert seen["correlation_id"] == "cid-201"
    assert seen["auth_header"].startswith("Bearer ")


@pytest.mark.unit
async def test_get_agent_authoring_draft_forwards_to_plant(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()

    async def _fake_get(self, draft_id, correlation_id=None, auth_header=None):
        assert draft_id == "AAD-1"
        assert correlation_id == "cid-202"
        assert auth_header and auth_header.startswith("Bearer ")
        return _draft_payload(status="changes_requested")

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.get_agent_authoring_draft",
        _fake_get,
    )

    response = await client.get(
        "/api/pp/agent-authoring/drafts/AAD-1",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-202"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "changes_requested"


@pytest.mark.unit
async def test_save_agent_authoring_draft_forwards_payload(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    seen = {}

    async def _fake_save(self, payload, correlation_id=None, auth_header=None):
        seen["payload"] = payload
        seen["correlation_id"] = correlation_id
        seen["auth_header"] = auth_header
        return _draft_payload()

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.save_agent_authoring_draft",
        _fake_save,
    )

    payload = {
        "candidate_agent_type_id": "marketing.digital_marketing_agent",
        "candidate_agent_label": "Digital Marketing Agent",
        "contract_payload": {"identity": {"name": "DMA"}},
        "section_states": {"identity": "ready"},
        "constraint_policy": {"approval_required": True},
    }

    response = await client.post(
        "/api/pp/agent-authoring/drafts",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "cid-203"},
        json=payload,
    )

    assert response.status_code == 200
    assert seen["payload"]["candidate_agent_label"] == "Digital Marketing Agent"
    assert seen["correlation_id"] == "cid-203"
    assert seen["auth_header"].startswith("Bearer ")


@pytest.mark.unit
async def test_submit_agent_authoring_draft_calls_audit(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []

    async def _fake_submit(self, draft_id, correlation_id=None, auth_header=None):
        assert draft_id == "AAD-1"
        return _draft_payload(status="in_review")

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.submit_agent_authoring_draft",
        _fake_submit,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    response = await client.post(
        "/api/pp/agent-authoring/drafts/AAD-1/submit",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_review"
    assert any(call["action"] == "draft_submitted_for_review" for call in audit_calls)


@pytest.mark.unit
async def test_request_changes_calls_audit_and_forwards_comments(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []
    seen = {}

    async def _fake_request_changes(self, draft_id, payload, correlation_id=None, auth_header=None):
        seen["draft_id"] = draft_id
        seen["payload"] = payload
        return {
            **_draft_payload(status="changes_requested"),
            "reviewer_comments": payload["reviewer_comments"],
        }

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.request_agent_authoring_changes",
        _fake_request_changes,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    response = await client.post(
        "/api/pp/agent-authoring/drafts/AAD-1/changes-requested",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reviewer_id": "reviewer-1",
            "reviewer_name": "Reviewer",
            "reviewer_comments": [
                {
                    "section_key": "identity",
                    "comment": "Clarify ICP.",
                    "severity": "changes_requested",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert seen["draft_id"] == "AAD-1"
    assert seen["payload"]["reviewer_comments"][0]["section_key"] == "identity"
    assert any(call["action"] == "draft_changes_requested" for call in audit_calls)


@pytest.mark.unit
async def test_approve_agent_authoring_draft_calls_audit(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    audit_calls = []

    async def _fake_approve(self, draft_id, payload, correlation_id=None, auth_header=None):
        assert draft_id == "AAD-1"
        assert payload["reviewer_name"] == "Approver"
        return _draft_payload(status="approved")

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr(
        "clients.plant_client.PlantAPIClient.approve_agent_authoring_draft",
        _fake_approve,
    )
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    response = await client.post(
        "/api/pp/agent-authoring/drafts/AAD-1/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"reviewer_id": "reviewer-2", "reviewer_name": "Approver"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert any(call["action"] == "draft_approved" for call in audit_calls)