from __future__ import annotations

import httpx
import pytest


class _FakeAsyncClient:
    def __init__(self, *, method: str, payload: dict, status_code: int = 200):
        self._method = method
        self._payload = payload
        self._status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url: str, params=None, timeout=None):
        req = httpx.Request("POST", url)
        return httpx.Response(self._status_code, json=self._payload, request=req)

    async def get(self, url: str, params=None, timeout=None):
        req = httpx.Request("GET", url)
        return httpx.Response(self._status_code, json=self._payload, request=req)


@pytest.mark.unit
async def test_run_audit_success(client, monkeypatch):
    import api.audit as audit

    payload = {"compliance_score": 100, "l0_breakdown": {}, "l1_breakdown": {}}
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(method="post", payload=payload))

    resp = await client.post("/api/pp/audit/run?entity_type=skill")
    assert resp.status_code == 200
    assert resp.json()["compliance_score"] == 100


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
    monkeypatch.setattr(audit.httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(method="get", payload=payload))

    resp = await client.get("/api/pp/audit/export?format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Compliance Score" in resp.text
