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
