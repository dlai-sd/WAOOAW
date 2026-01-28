from __future__ import annotations

import pytest

from core.config import settings


@pytest.mark.auth
async def test_admin_me_requires_google_client_id(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "", raising=False)
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 503


@pytest.mark.auth
async def test_admin_me_success(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client", raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "test", raising=False)

    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "google"
    assert data["environment"] == "test"
