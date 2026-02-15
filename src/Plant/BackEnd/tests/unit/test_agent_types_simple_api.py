from __future__ import annotations


def test_list_agent_types_returns_two_definitions(test_client):
    res = test_client.get("/api/v1/agent-types")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    ids = {x.get("agent_type_id") for x in data}
    assert ids == {"marketing.digital_marketing.v1", "trading.share_trader.v1"}


def test_get_agent_type_by_id(test_client):
    res = test_client.get("/api/v1/agent-types/marketing.digital_marketing.v1")
    assert res.status_code == 200
    data = res.json()
    assert data["agent_type_id"] == "marketing.digital_marketing.v1"
    assert data.get("display_name") == "Digital Marketing"
    assert data["version"]
    assert isinstance(data.get("config_schema", {}).get("fields"), list)
    assert isinstance(data.get("goal_templates"), list)


def test_get_agent_type_by_legacy_id_returns_canonical(test_client):
    res = test_client.get("/api/v1/agent-types/marketing.healthcare.v1")
    assert res.status_code == 200
    data = res.json()
    assert data["agent_type_id"] == "marketing.digital_marketing.v1"


def test_get_unknown_agent_type_returns_404(test_client):
    res = test_client.get("/api/v1/agent-types/does.not.exist")
    assert res.status_code == 404


def test_upsert_agent_type_updates_definition(test_client):
    existing = test_client.get("/api/v1/agent-types/marketing.digital_marketing.v1")
    assert existing.status_code == 200
    payload = existing.json()
    payload["version"] = "1.0.1"

    res = test_client.put("/api/v1/agent-types/marketing.digital_marketing.v1", json=payload)
    assert res.status_code == 200
    assert res.json()["version"] == "1.0.1"

    after = test_client.get("/api/v1/agent-types/marketing.digital_marketing.v1")
    assert after.status_code == 200
    assert after.json()["version"] == "1.0.1"


def test_upsert_agent_type_rejects_id_mismatch(test_client):
    payload = {
        "agent_type_id": "trading.share_trader.v1",
        "version": "9.9.9",
        "config_schema": {"fields": []},
        "goal_templates": [],
        "enforcement_defaults": {"approval_required": True, "deterministic": False},
    }
    res = test_client.put("/api/v1/agent-types/marketing.digital_marketing.v1", json=payload)
    assert res.status_code == 400
