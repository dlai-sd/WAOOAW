from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_upsert_and_list_agent_setup_persists_encrypted_refs(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    payload = {
        "customer_id": "CUST-001",
        "agent_id": "AGT-MKT-HEALTH-001",
        "channels": ["linkedin", "instagram"],
        "posting_identity": "Care Clinic",
        "credential_refs": {"linkedin": "credref-link-1", "instagram": "credref-ig-1"},
    }

    upsert = await client.put("/api/pp/agent-setups", json=payload)
    assert upsert.status_code == 200
    body = upsert.json()
    assert body["customer_id"] == "CUST-001"
    assert body["agent_id"] == "AGT-MKT-HEALTH-001"
    assert set(body["channels"]) == {"linkedin", "instagram"}
    assert body["credential_refs"]["linkedin"] == "credref-link-1"

    raw = store_path.read_text(encoding="utf-8")
    assert "credref-link-1" not in raw
    assert "credref-ig-1" not in raw

    listed = await client.get("/api/pp/agent-setups", params={"customer_id": "CUST-001", "agent_id": "AGT-MKT-HEALTH-001"})
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body["count"] == 1
    assert listed_body["setups"][0]["credential_refs"]["instagram"] == "credref-ig-1"
