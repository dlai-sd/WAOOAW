from __future__ import annotations

import httpx
import pytest

from core.config import settings


class _FakeAsyncClient:
    def __init__(self, *, method: str, payload: dict, status_code: int = 200):
        self._method = method
        self._payload = payload
        self._status_code = status_code
        self.last_headers = None
        self.last_params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url: str, params=None, headers=None, timeout=None):
        self.last_headers = headers
        self.last_params = params
        req = httpx.Request("POST", url)
        return httpx.Response(self._status_code, json=self._payload, request=req)

    async def get(self, url: str, params=None, headers=None, timeout=None):
        self.last_headers = headers
        self.last_params = params
        req = httpx.Request("GET", url)
        return httpx.Response(self._status_code, json=self._payload, request=req)


@pytest.mark.unit
async def test_run_audit_success(client, monkeypatch):
    import api.audit as audit

    payload = {"compliance_score": 100, "l0_breakdown": {}, "l1_breakdown": {}}
    fake = _FakeAsyncClient(method="post", payload=payload)
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: fake)

    resp = await client.post(
        "/api/pp/audit/run?entity_type=skill",
        headers={"authorization": "Bearer test", "x-correlation-id": "cid-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["compliance_score"] == 100
    assert fake.last_headers["Authorization"] == "Bearer test"
    assert fake.last_headers["X-Correlation-ID"] == "cid-1"


@pytest.mark.unit
async def test_export_csv_success(client, monkeypatch):
    import api.audit as audit

    payload = {
        "compliance_score": 90,
        "total_entities": 1,
        "total_violations": 0,
        "timestamp": "2026-01-01T00:00:00Z",
        "l0_breakdown": {"L0-01": {"violations": 0}},
        "l1_breakdown": {"L1-01": {"violations": 0}},
    }
    fake = _FakeAsyncClient(method="get", payload=payload)
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: fake)

    resp = await client.get(
        "/api/pp/audit/export?format=csv",
        headers={"authorization": "Bearer test", "x-correlation-id": "cid-2"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Compliance Score" in resp.text
    assert fake.last_headers["Authorization"] == "Bearer test"
    assert fake.last_headers["X-Correlation-ID"] == "cid-2"


@pytest.mark.unit
async def test_detect_tampering_success(client, monkeypatch):
    import api.audit as audit

    payload = {"tampering_detected": False, "entity_id": "agent-1"}
    fake = _FakeAsyncClient(method="get", payload=payload)
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: fake)

    resp = await client.get(
        "/api/pp/audit/tampering/agent-1",
        headers={"authorization": "Bearer test", "x-correlation-id": "cid-3"},
    )
    assert resp.status_code == 200
    assert resp.json()["tampering_detected"] is False
    assert fake.last_headers["Authorization"] == "Bearer test"
    assert fake.last_headers["X-Correlation-ID"] == "cid-3"


@pytest.mark.unit
async def test_export_json_success(client, monkeypatch):
    import api.audit as audit

    payload = {"compliance_score": 77, "timestamp": "2026-01-01T00:00:00Z"}
    fake = _FakeAsyncClient(method="get", payload=payload)
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: fake)

    resp = await client.get(
        "/api/pp/audit/export",
        headers={"authorization": "Bearer test", "x-correlation-id": "cid-4"},
    )
    assert resp.status_code == 200
    assert resp.json()["compliance_score"] == 77
    assert fake.last_headers["Authorization"] == "Bearer test"
    assert fake.last_headers["X-Correlation-ID"] == "cid-4"


@pytest.mark.unit
async def test_google_verify_calls_audit_log(client, monkeypatch):
    """E4-S1-T2: POST /auth/google/verify emits audit log with screen='pp_auth'."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client", raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "ALLOWED_EMAIL_DOMAINS", "waooaw.com", raising=False)

    audit_calls = []

    def _mock_verify(id_token_str, request, audience):
        return {
            "aud": "test-client",
            "iss": "accounts.google.com",
            "email": "admin@waooaw.com",
            "email_verified": True,
            "sub": "google-sub-audit-test",
        }

    async def _fake_audit_log(self, screen, action, outcome, **kwargs):
        audit_calls.append({"screen": screen, "action": action, "outcome": outcome})

    monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", _mock_verify)
    monkeypatch.setattr("services.audit_dependency.AuditLogger.log", _fake_audit_log)

    resp = await client.post("/api/auth/google/verify", json={"credential": "fake"})
    assert resp.status_code == 200
    assert any(c["screen"] == "pp_auth" for c in audit_calls)
