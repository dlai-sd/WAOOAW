from __future__ import annotations


def test_razorpay_order_disabled_when_not_razorpay_mode(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    res = client.post(
        "/api/cp/payments/razorpay/order",
        headers=auth_headers,
        json={"agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 403


def test_razorpay_order_delegates_to_plant_when_configured(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")
    monkeypatch.setenv("CP_PAYMENTS_USE_PLANT", "true")

    from api import payments_razorpay as payments_razorpay_api

    async def _fake_razorpay_order_in_plant(*, agent_id: str, duration: str, customer_id: str, authorization: str | None):
        assert agent_id == "agent-123"
        assert duration == "monthly"
        assert customer_id
        assert authorization and authorization.startswith("Bearer ")
        return {
            "order_id": "ORDER-plant-1",
            "subscription_id": "SUB-plant-1",
            "amount": 12000,
            "currency": "INR",
            "razorpay_key_id": "rzp_test_key",
            "razorpay_order_id": "order_test_1",
        }

    monkeypatch.setattr(payments_razorpay_api, "_razorpay_order_in_plant", _fake_razorpay_order_in_plant)

    res = client.post(
        "/api/cp/payments/razorpay/order",
        headers=auth_headers,
        json={"agent_id": "agent-123", "duration": "monthly"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["payment_provider"] == "razorpay"
    assert body["order_id"] == "ORDER-plant-1"
    assert body["subscription_id"] == "SUB-plant-1"
    assert body["amount"] == 12000
    assert body["currency"] == "INR"
    assert body["razorpay_key_id"] == "rzp_test_key"
    assert body["razorpay_order_id"] == "order_test_1"


def test_razorpay_confirm_delegates_to_plant_when_configured(client, auth_headers, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")
    monkeypatch.setenv("CP_PAYMENTS_USE_PLANT", "true")

    from api import payments_razorpay as payments_razorpay_api

    async def _fake_razorpay_confirm_in_plant(
        *,
        order_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        customer_id: str,
        authorization: str | None,
    ):
        assert order_id == "ORDER-1"
        assert razorpay_order_id == "order_rzp_1"
        assert razorpay_payment_id == "pay_1"
        assert razorpay_signature == "sig_1"
        assert customer_id
        assert authorization and authorization.startswith("Bearer ")
        return {"order_id": "ORDER-1", "subscription_id": "SUB-1", "subscription_status": "active"}

    monkeypatch.setattr(payments_razorpay_api, "_razorpay_confirm_in_plant", _fake_razorpay_confirm_in_plant)

    res = client.post(
        "/api/cp/payments/razorpay/confirm",
        headers=auth_headers,
        json={
            "order_id": "ORDER-1",
            "razorpay_order_id": "order_rzp_1",
            "razorpay_payment_id": "pay_1",
            "razorpay_signature": "sig_1",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["payment_provider"] == "razorpay"
    assert body["order_id"] == "ORDER-1"
    assert body["subscription_id"] == "SUB-1"
    assert body["subscription_status"] == "active"
