from __future__ import annotations


def test_coupon_checkout_happy_path(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    res = client.post(
        "/api/cp/payments/coupon/checkout",
        headers=auth_headers,
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["payment_provider"] == "coupon"
    assert body["amount"] == 0
    assert body["currency"] == "INR"
    assert body["coupon_code"] == "WAOOAW100"
    assert body["agent_id"] == "agent-123"
    assert body["duration"] == "monthly"
    assert body["order_id"].startswith("ORDER-")


def test_coupon_checkout_delegates_to_plant_when_configured(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")
    monkeypatch.setenv("CP_PAYMENTS_USE_PLANT", "true")

    from api import payments_coupon as payments_coupon_api

    async def _fake_coupon_checkout_in_plant(*, coupon_code: str, agent_id: str, duration: str, customer_id, authorization, idempotency_key):
        assert coupon_code == "WAOOAW100"
        assert agent_id == "agent-123"
        assert duration == "monthly"
        assert authorization and authorization.startswith("Bearer ")
        assert idempotency_key == "idem-123"
        return {"order_id": "ORDER-plant-123", "subscription_id": "SUB-plant-456"}

    monkeypatch.setattr(payments_coupon_api, "_coupon_checkout_in_plant", _fake_coupon_checkout_in_plant)

    res = client.post(
        "/api/cp/payments/coupon/checkout",
        headers={**auth_headers, "Idempotency-Key": "idem-123"},
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["order_id"] == "ORDER-plant-123"
    assert body["subscription_id"] == "SUB-plant-456"


def test_coupon_checkout_rejects_invalid_code(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    res = client.post(
        "/api/cp/payments/coupon/checkout",
        headers=auth_headers,
        json={"coupon_code": "NOPE", "agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 400


def test_coupon_checkout_disabled_when_not_coupon_mode(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")

    res = client.post(
        "/api/cp/payments/coupon/checkout",
        headers=auth_headers,
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 403
