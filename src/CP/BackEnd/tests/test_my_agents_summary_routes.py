from __future__ import annotations

import pytest
from datetime import datetime, timezone


def test_cp_my_agents_summary_cp_local(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("CP_PAYMENTS_USE_PLANT", "false")
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "false")

    checkout = client.post(
        "/api/cp/payments/coupon/checkout",
        headers=auth_headers,
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    summary = client.get("/api/cp/my-agents/summary", headers=auth_headers)
    assert summary.status_code == 200
    payload = summary.json()
    assert isinstance(payload.get("instances"), list)
    assert any(x.get("subscription_id") == subscription_id for x in payload["instances"])


def test_cp_my_agents_summary_delegates_subscription_listing_to_plant(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import my_agents_summary as summary_api

    async def _fake_plant_get_json(*, url: str, authorization: str | None):
        assert authorization and authorization.startswith("Bearer ")
        if "/by-customer/" in url:
            return [
                {
                    "subscription_id": "SUB-plant-1",
                    "agent_id": "agent-123",
                    "duration": "monthly",
                    "customer_id": user_id,
                    "status": "active",
                    "current_period_start": "2026-02-01T00:00:00+00:00",
                    "current_period_end": "2026-03-01T00:00:00+00:00",
                    "cancel_at_period_end": False,
                }
            ]
        # hired-agents enrichment can be absent; act like not found
        raise summary_api.HTTPException(status_code=404, detail="not found")

    monkeypatch.setattr(summary_api, "_plant_get_json", _fake_plant_get_json)

    summary = client.get("/api/cp/my-agents/summary", headers=auth_headers)
    assert summary.status_code == 200
    items = summary.json()["instances"]
    assert items[0]["subscription_id"] == "SUB-plant-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_subscriptions_plant_mode_rejects_non_list(monkeypatch):
    from api import my_agents_summary as api

    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant")

    async def _fake_get_json(**_kwargs):
        return {"not": "a-list"}

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)

    with pytest.raises(api.HTTPException) as exc:
        await api._list_subscriptions(customer_id="CUST-1", authorization="Bearer t")
    assert exc.value.status_code == 502


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_subscriptions_plant_mode_requires_base_url(monkeypatch):
    from api import my_agents_summary as api

    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    with pytest.raises(api.HTTPException) as exc:
        await api._list_subscriptions(customer_id="CUST-1", authorization=None)
    assert exc.value.status_code == 503


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enrich_with_hired_agent_ignores_404(monkeypatch):
    from api import my_agents_summary as api

    async def _fake_get_json(**_kwargs):
        raise api.HTTPException(status_code=404, detail="not found")

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)

    instance = api.MyAgentInstanceSummary(
        subscription_id="SUB-404",
        agent_id="agent-1",
        duration="monthly",
        status="active",
        current_period_start="2026-02-01T00:00:00+00:00",
        current_period_end="2026-03-01T00:00:00+00:00",
        cancel_at_period_end=False,
    )
    enriched = await api._enrich_with_hired_agent(
        base_url="http://plant",
        authorization="Bearer t",
        customer_id="CUST-1",
        instance=instance,
    )
    assert enriched == instance


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enrich_with_hired_agent_maps_datetime_fields(monkeypatch):
    from api import my_agents_summary as api

    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    async def _fake_get_json(**_kwargs):
        return {
            "hired_instance_id": "HI-1",
            "agent_type_id": "trading.share_trader.v1",
            "nickname": "Alpha",
            "configured": True,
            "goals_completed": False,
            "trial_status": "active",
            "trial_start_at": now,
            "trial_end_at": now,
            "subscription_status": "active",
            "subscription_ended_at": None,
            "retention_expires_at": now,
        }

    monkeypatch.setattr(api, "_plant_get_json", _fake_get_json)

    instance = api.MyAgentInstanceSummary(
        subscription_id="SUB-1",
        agent_id="agent-1",
        duration="monthly",
        status="active",
        current_period_start="2026-02-01T00:00:00+00:00",
        current_period_end="2026-03-01T00:00:00+00:00",
        cancel_at_period_end=False,
    )

    enriched = await api._enrich_with_hired_agent(
        base_url="http://plant",
        authorization="Bearer t",
        customer_id="CUST-1",
        instance=instance,
    )
    assert enriched.hired_instance_id == "HI-1"
    assert enriched.trial_start_at == now.isoformat()
    assert enriched.retention_expires_at == now.isoformat()
