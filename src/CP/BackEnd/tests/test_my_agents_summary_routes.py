from __future__ import annotations


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
