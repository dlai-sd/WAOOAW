from __future__ import annotations


def test_hire_wizard_draft_is_persisted_cp_local(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "false")

    r1 = client.put(
        "/api/cp/hire/wizard/draft",
        headers=auth_headers,
        json={
            "subscription_id": "SUB-1",
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Nick",
            "theme": "dark",
            "config": {"a": 1},
        },
    )
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["subscription_id"] == "SUB-1"
    assert b1["agent_type_id"] == "marketing.digital_marketing.v1"
    assert b1["configured"] is True
    assert b1["trial_status"] == "not_started"

    r2 = client.get("/api/cp/hire/wizard/by-subscription/SUB-1", headers=auth_headers)
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["hired_instance_id"] == b1["hired_instance_id"]
    assert b2["agent_type_id"] == "marketing.digital_marketing.v1"
    assert b2["config"]["a"] == 1


def test_hire_wizard_delegates_to_plant_when_enabled(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api

    async def _fake_plant_upsert_draft(*, body, customer_id, authorization):
        assert authorization and authorization.startswith("Bearer ")
        assert body.subscription_id == "SUB-plant"
        assert body.agent_type_id == "marketing.digital_marketing.v1"
        assert customer_id
        return {
            "hired_instance_id": "HAI-plant-1",
            "subscription_id": "SUB-plant",
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Nick",
            "theme": "dark",
            "config": {"x": True},
            "configured": True,
            "goals_completed": False,
            "subscription_status": "active",
            "trial_status": "not_started",
            "trial_start_at": None,
            "trial_end_at": None,
        }

    monkeypatch.setattr(hire_wizard_api, "_plant_upsert_draft", _fake_plant_upsert_draft)

    r = client.put(
        "/api/cp/hire/wizard/draft",
        headers=auth_headers,
        json={
            "subscription_id": "SUB-plant",
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Nick",
            "theme": "dark",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["hired_instance_id"] == "HAI-plant-1"
    assert body["subscription_id"] == "SUB-plant"
    assert body["agent_type_id"] == "marketing.digital_marketing.v1"
    assert body["subscription_status"] == "active"


def test_hire_wizard_finalize_delegates_to_plant_when_enabled(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api

    async def _fake_plant_finalize(*, hired_instance_id: str, agent_type_id: str, goals_completed: bool, customer_id, authorization):
        assert hired_instance_id == "HAI-plant-1"
        assert agent_type_id == "marketing.digital_marketing.v1"
        assert goals_completed is True
        assert customer_id
        assert authorization and authorization.startswith("Bearer ")
        return {
            "hired_instance_id": "HAI-plant-1",
            "subscription_id": "SUB-plant",
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Nick",
            "theme": "dark",
            "config": {},
            "configured": True,
            "goals_completed": True,
            "subscription_status": "active",
            "trial_status": "active",
            "trial_start_at": "2026-02-08T00:00:00Z",
            "trial_end_at": "2026-02-15T00:00:00Z",
        }

    monkeypatch.setattr(hire_wizard_api, "_plant_finalize", _fake_plant_finalize)

    r = client.post(
        "/api/cp/hire/wizard/finalize",
        headers=auth_headers,
        json={"hired_instance_id": "HAI-plant-1", "agent_type_id": "marketing.digital_marketing.v1", "goals_completed": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["trial_status"] == "active"
    assert body["goals_completed"] is True
    assert body["agent_type_id"] == "marketing.digital_marketing.v1"


def test_hire_wizard_get_by_subscription_delegates_to_plant(client, auth_headers, monkeypatch):
    """When CP_HIRE_USE_PLANT=true, GET by-subscription proxies to Plant and returns persisted data."""
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api

    async def _fake_plant_get_by_subscription(*, subscription_id: str, authorization):
        assert subscription_id == "SUB-plant-get"
        assert authorization and authorization.startswith("Bearer ")
        return {
            "hired_instance_id": "HAI-plant-get-1",
            "subscription_id": "SUB-plant-get",
            "agent_id": "agent-999",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "MyAgent",
            "theme": "light",
            "config": {"k": "v"},
            "configured": True,
            "goals_completed": False,
            "subscription_status": "active",
            "trial_status": "active",
            "trial_start_at": "2026-03-01T00:00:00Z",
            "trial_end_at": "2026-03-08T00:00:00Z",
        }

    monkeypatch.setattr(hire_wizard_api, "_plant_get_by_subscription", _fake_plant_get_by_subscription)

    r = client.get("/api/cp/hire/wizard/by-subscription/SUB-plant-get", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["hired_instance_id"] == "HAI-plant-get-1"
    assert body["trial_status"] == "active"
    assert body["trial_start_at"] == "2026-03-01T00:00:00Z"
    assert body["config"]["k"] == "v"
    assert body["subscription_status"] == "active"


def test_hire_wizard_get_by_subscription_plant_404_propagates(client, auth_headers, monkeypatch):
    """When Plant returns 404, the 404 is propagated to the caller (hired instance not found)."""
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api
    from fastapi import HTTPException as FastAPIHTTPException

    async def _fake_plant_get_by_subscription(*, subscription_id: str, authorization):
        raise FastAPIHTTPException(status_code=404, detail="Plant get by-subscription failed (404)")

    monkeypatch.setattr(hire_wizard_api, "_plant_get_by_subscription", _fake_plant_get_by_subscription)

    r = client.get("/api/cp/hire/wizard/by-subscription/SUB-missing", headers=auth_headers)
    assert r.status_code == 404


def test_hire_wizard_get_by_subscription_fallback_to_local_when_plant_unavailable(
    client, auth_headers, monkeypatch
):
    """AC-4: When CP_HIRE_USE_PLANT=true but PLANT_GATEWAY_URL unset, RuntimeError is caught
    and the route falls through to the CP-local in-memory dict."""
    # Seed the in-memory draft
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "false")
    client.put(
        "/api/cp/hire/wizard/draft",
        headers=auth_headers,
        json={
            "subscription_id": "SUB-fallback",
            "agent_id": "agent-fallback",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "Fallback",
            "theme": "dark",
        },
    )

    # Now flip the flag on but leave PLANT_GATEWAY_URL unset → RuntimeError → fallback
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    r = client.get("/api/cp/hire/wizard/by-subscription/SUB-fallback", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["subscription_id"] == "SUB-fallback"
    assert body["nickname"] == "Fallback"
