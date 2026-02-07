from __future__ import annotations

from pathlib import Path


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
