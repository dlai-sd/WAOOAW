from __future__ import annotations


def test_cp_subscriptions_list_and_cancel_cp_local(client, auth_headers, monkeypatch):
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

    listed = client.get("/api/cp/subscriptions/", headers=auth_headers)
    assert listed.status_code == 200
    items = listed.json()
    assert any(x["subscription_id"] == subscription_id for x in items)

    cancel = client.post(f"/api/cp/subscriptions/{subscription_id}/cancel", headers=auth_headers)
    assert cancel.status_code == 200
    assert cancel.json()["cancel_at_period_end"] is True


def test_cp_subscriptions_delegates_to_plant_when_enabled(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import subscriptions as subs_api

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
        return {
            "subscription_id": "SUB-plant-1",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": user_id,
            "status": "active",
            "current_period_start": "2026-02-01T00:00:00+00:00",
            "current_period_end": "2026-03-01T00:00:00+00:00",
            "cancel_at_period_end": False,
        }

    async def _fake_plant_post_json(*, url: str, authorization: str | None, params: dict | None = None):
        assert authorization and authorization.startswith("Bearer ")
        assert params and params.get("customer_id") == user_id
        return {
            "subscription_id": "SUB-plant-1",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": user_id,
            "status": "active",
            "current_period_start": "2026-02-01T00:00:00+00:00",
            "current_period_end": "2026-03-01T00:00:00+00:00",
            "cancel_at_period_end": True,
        }

    monkeypatch.setattr(subs_api, "_plant_get_json", _fake_plant_get_json)
    monkeypatch.setattr(subs_api, "_plant_post_json", _fake_plant_post_json)

    listed = client.get("/api/cp/subscriptions/", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["subscription_id"] == "SUB-plant-1"

    cancel = client.post("/api/cp/subscriptions/SUB-plant-1/cancel", headers=auth_headers)
    assert cancel.status_code == 200
    assert cancel.json()["cancel_at_period_end"] is True


def test_cp_subscriptions_get_single_plant_mode(client, auth_headers, monkeypatch):
    """Test getting single subscription from Plant."""
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    from api import subscriptions as subs_api

    async def _fake_plant_get_json(*, url: str, authorization: str | None):
        return {
            "subscription_id": "SUB-single",
            "agent_id": "agent-456",
            "duration": "annual",
            "customer_id": user_id,
            "status": "active",
            "current_period_start": "2026-01-01T00:00:00+00:00",
            "current_period_end": "2027-01-01T00:00:00+00:00",
            "cancel_at_period_end": False,
        }

    monkeypatch.setattr(subs_api, "_plant_get_json", _fake_plant_get_json)

    resp = client.get("/api/cp/subscriptions/SUB-single", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["subscription_id"] == "SUB-single"


def test_cp_subscriptions_get_plant_mode_authz_failure(client, auth_headers, monkeypatch):
    """Test subscription authz failure when customer_id mismatch."""
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import subscriptions as subs_api

    async def _fake_plant_get_json(*, url: str, authorization: str | None):
        return {
            "subscription_id": "SUB-other-user",
            "agent_id": "agent-789",
            "duration": "monthly",
            "customer_id": "some-other-user-id",
            "status": "active",
            "current_period_start": "2026-01-01T00:00:00+00:00",
            "current_period_end": "2026-02-01T00:00:00+00:00",
            "cancel_at_period_end": False,
        }

    monkeypatch.setattr(subs_api, "_plant_get_json", _fake_plant_get_json)

    resp = client.get("/api/cp/subscriptions/SUB-other-user", headers=auth_headers)
    assert resp.status_code == 403  # Forbidden


def test_cp_subscriptions_plant_network_error_fallback(client, auth_headers, monkeypatch):
    """Test fallback to CP-local when Plant network fails."""
    monkeypatch.setenv("CP_SUBSCRIPTIONS_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import subscriptions as subs_api

    async def _fake_plant_get_json(*, url: str, authorization: str | None):
        raise RuntimeError("Plant call failed (network)")

    monkeypatch.setattr(subs_api, "_plant_get_json", _fake_plant_get_json)

    # Should fallback to CP-local (empty since no subscriptions created)
    resp = client.get("/api/cp/subscriptions/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
