from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock


def test_platform_credentials_upsert_and_list(client, auth_headers, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "cp_platform_credentials.jsonl"
    monkeypatch.setenv("CP_PLATFORM_CREDENTIALS_STORE_PATH", str(store_path))
    monkeypatch.setenv("CP_PLATFORM_CREDENTIALS_SECRET", "test-secret")

    from services import platform_credentials as svc

    svc.default_platform_credential_store.cache_clear()

    upsert = client.put(
        "/api/cp/platform-credentials",
        headers=auth_headers,
        json={
            "platform": "instagram",
            "posting_identity": "clinic-1",
            "access_token": "secret-token",
            "refresh_token": "refresh-token",
        },
    )
    assert upsert.status_code == 200
    body = upsert.json()
    assert body["platform"] == "instagram"
    assert body["posting_identity"] == "clinic-1"
    assert body["credential_ref"].startswith("CRED-")
    assert "access_token" not in body
    assert "refresh_token" not in body

    listed = client.get("/api/cp/platform-credentials", headers=auth_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["credential_ref"] == body["credential_ref"]


def test_connect_youtube_credential_ref_proxies_to_plant(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-test:8000")

    from main import app
    from api.platform_credentials import get_plant_gateway_client

    fake = AsyncMock()
    fake.request_json.return_value = type(
        "R",
        (),
        {
            "status_code": 201,
            "json": {
                "id": "conn-1",
                "hired_instance_id": "HIRED-1",
                "skill_id": "skill-1",
                "platform_key": "youtube",
                "status": "pending",
            },
            "headers": {},
        },
    )()
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    resp = client.post(
        "/api/cp/platform-credentials/youtube",
        headers=auth_headers,
        json={
            "hired_instance_id": "HIRED-1",
            "skill_id": "skill-1",
            "credential_ref": "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["platform_key"] == "youtube"
    fake.request_json.assert_awaited_once()
    app.dependency_overrides.clear()
