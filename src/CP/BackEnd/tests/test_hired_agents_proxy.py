from __future__ import annotations

import httpx
import pytest


@pytest.mark.unit
def test_cp_hired_agents_get_by_subscription_injects_customer_id(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import hired_agents_proxy as api

    async def _fake_get_json(*, url: str, authorization: str | None, correlation_id: str | None):
        assert authorization and authorization.startswith("Bearer ")
        assert f"customer_id={user_id}" in url
        return {
            "hired_instance_id": "HAI-1",
            "subscription_id": "SUB-1",
            "agent_id": "AGT-TRD-DELTA-001",
            "agent_type_id": "trading.delta_futures.v1",
            "nickname": "Trader",
            "theme": "dark",
            "config": {},
            "configured": False,
            "goals_completed": False,
            "trial_status": "not_started",
        }

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)

    resp = client.get("/api/cp/hired-agents/by-subscription/SUB-1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscription_id"] == "SUB-1"
    assert body["agent_type_id"] == "trading.delta_futures.v1"


@pytest.mark.unit
def test_cp_hired_agents_returns_503_when_plant_url_missing(client, auth_headers, monkeypatch):
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    resp = client.get("/api/cp/hired-agents/by-subscription/SUB-1", headers=auth_headers)
    assert resp.status_code == 503


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plant_get_json_converts_network_error_to_runtime_error(monkeypatch):
    from api import hired_agents_proxy as api

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *_args, **_kwargs):
            raise httpx.RequestError("boom")

    monkeypatch.setattr(api.httpx, "AsyncClient", lambda timeout=10.0: _FakeClient())

    with pytest.raises(RuntimeError):
        await api._plant_get_json(url="http://plant/x", authorization="Bearer t", correlation_id="cid")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plant_get_json_rejects_non_dict_payload(monkeypatch):
    from api import hired_agents_proxy as api

    class _Resp:
        status_code = 200

        def json(self):
            return ["not-a-dict"]

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *_args, **_kwargs):
            return _Resp()

    monkeypatch.setattr(api.httpx, "AsyncClient", lambda timeout=10.0: _FakeClient())

    with pytest.raises(api.HTTPException) as exc:
        await api._plant_get_json(url="http://plant/x", authorization=None, correlation_id=None)
    assert exc.value.status_code == 502


@pytest.mark.unit
def test_cp_hired_agents_put_draft_injects_customer_id(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import hired_agents_proxy as api

    async def _fake_put_json(*, url: str, authorization: str | None, correlation_id: str | None, payload: dict):
        assert authorization and authorization.startswith("Bearer ")
        assert payload.get("customer_id") == user_id
        assert payload.get("subscription_id") == "SUB-1"
        assert payload.get("agent_id") == "AGT-MKT-HEALTH-001"
        return {
            "hired_instance_id": "HAI-2",
            "subscription_id": "SUB-1",
            "agent_id": "AGT-MKT-HEALTH-001",
            "agent_type_id": "marketing.healthcare.v1",
            "nickname": payload.get("nickname"),
            "theme": payload.get("theme"),
            "config": payload.get("config") or {},
            "configured": False,
            "goals_completed": False,
            "trial_status": "not_started",
        }

    monkeypatch.setattr(api, "_plant_put_json", _fake_put_json)

    resp = client.put(
        "/api/cp/hired-agents/draft",
        headers=auth_headers,
        json={
            "subscription_id": "SUB-1",
            "agent_id": "AGT-MKT-HEALTH-001",
            "nickname": "Marketer",
            "theme": "dark",
            "config": {"platforms_enabled": ["instagram"], "platform_credentials": {"instagram": "CRED-1"}},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["hired_instance_id"] == "HAI-2"


@pytest.mark.unit
def test_cp_hired_agents_goals_inject_customer_id_and_forward(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import hired_agents_proxy as api

    async def _fake_get_json(*, url: str, authorization: str | None, correlation_id: str | None):
        assert authorization and authorization.startswith("Bearer ")
        assert f"customer_id={user_id}" in url
        return {"hired_instance_id": "HAI-1", "goals": []}

    async def _fake_put_json(*, url: str, authorization: str | None, correlation_id: str | None, payload: dict):
        assert authorization and authorization.startswith("Bearer ")
        assert payload.get("customer_id") == user_id
        assert payload.get("goal_template_id") == "trading.trade_intent_draft.v1"
        return {
            "goal_instance_id": "GOI-1",
            "hired_instance_id": "HAI-1",
            "goal_template_id": payload.get("goal_template_id"),
            "frequency": payload.get("frequency"),
            "settings": payload.get("settings") or {},
        }

    async def _fake_delete_json(*, url: str, authorization: str | None, correlation_id: str | None):
        assert authorization and authorization.startswith("Bearer ")
        assert f"customer_id={user_id}" in url
        assert "goal_instance_id=GOI-1" in url
        return {"deleted": True, "goal_instance_id": "GOI-1"}

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)
    monkeypatch.setattr(api, "_plant_put_json", _fake_put_json)
    monkeypatch.setattr(api, "_plant_delete_json", _fake_delete_json)

    resp_list = client.get("/api/cp/hired-agents/HAI-1/goals", headers=auth_headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["hired_instance_id"] == "HAI-1"

    resp_put = client.put(
        "/api/cp/hired-agents/HAI-1/goals",
        headers=auth_headers,
        json={
            "goal_template_id": "trading.trade_intent_draft.v1",
            "frequency": "on_demand",
            "settings": {"coin": "BTC", "side": "buy", "units": 1},
        },
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["goal_instance_id"] == "GOI-1"

    resp_del = client.delete("/api/cp/hired-agents/HAI-1/goals?goal_instance_id=GOI-1", headers=auth_headers)
    assert resp_del.status_code == 200
    assert resp_del.json()["deleted"] is True


@pytest.mark.unit
def test_cp_hired_agents_deliverables_inject_customer_id_and_forward(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import hired_agents_proxy as api

    async def _fake_get_json(*, url: str, authorization: str | None, correlation_id: str | None):
        assert authorization and authorization.startswith("Bearer ")
        assert f"customer_id={user_id}" in url
        assert "/api/v1/hired-agents/HAI-1/deliverables" in url
        return {"hired_instance_id": "HAI-1", "deliverables": []}

    async def _fake_post_json(*, url: str, authorization: str | None, correlation_id: str | None, payload: dict):
        assert authorization and authorization.startswith("Bearer ")
        assert payload.get("customer_id") == user_id
        if url.endswith("/review"):
            assert payload.get("decision") == "approved"
            return {
                "deliverable_id": "DEL-1",
                "review_status": "approved",
                "approval_id": "APR-1",
                "updated_at": "now",
            }
        if url.endswith("/execute"):
            assert payload.get("approval_id") == "APR-1"
            return {
                "deliverable_id": "DEL-1",
                "execution_status": "executed",
                "executed_at": "now",
                "updated_at": "now",
            }
        raise AssertionError("unexpected url")

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)
    monkeypatch.setattr(api, "_plant_post_json", _fake_post_json)

    resp_list = client.get("/api/cp/hired-agents/HAI-1/deliverables", headers=auth_headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["hired_instance_id"] == "HAI-1"

    resp_review = client.post(
        "/api/cp/hired-agents/deliverables/DEL-1/review",
        headers=auth_headers,
        json={"decision": "approved", "notes": "LGTM"},
    )
    assert resp_review.status_code == 200
    assert resp_review.json()["approval_id"] == "APR-1"

    resp_execute = client.post(
        "/api/cp/hired-agents/deliverables/DEL-1/execute",
        headers=auth_headers,
        json={"approval_id": "APR-1"},
    )
    assert resp_execute.status_code == 200
    assert resp_execute.json()["execution_status"] == "executed"
