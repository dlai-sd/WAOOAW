import pytest


@pytest.mark.unit
def test_plant_coupon_checkout_creates_order_and_subscription(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_id"].startswith("ORDER-")
    assert body["subscription_id"].startswith("SUB-")
    assert body["payment_provider"] == "coupon"
    assert body["amount"] == 0
    assert body["currency"] == "INR"
    assert body["coupon_code"] == "WAOOAW100"
    assert body["agent_id"] == "agent-123"
    assert body["duration"] == "monthly"
    assert body["subscription_status"] == "active"
    assert body["trial_status"] == "not_started"


@pytest.mark.unit
def test_plant_coupon_checkout_rejects_invalid_code(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={"coupon_code": "NOPE", "agent_id": "agent-123", "duration": "monthly"},
    )
    assert resp.status_code == 400


@pytest.mark.unit
def test_plant_coupon_checkout_disabled_when_not_coupon_mode(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")

    resp = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly"},
    )
    assert resp.status_code == 403


@pytest.mark.unit
def test_plant_coupon_checkout_idempotency_key_replays_same_response(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    payload = {"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly", "customer_id": "cust-1"}
    headers = {"Idempotency-Key": "idem-abc"}

    r1 = test_client.post("/api/v1/payments/coupon/checkout", json=payload, headers=headers)
    assert r1.status_code == 200
    b1 = r1.json()

    r2 = test_client.post("/api/v1/payments/coupon/checkout", json=payload, headers=headers)
    assert r2.status_code == 200
    b2 = r2.json()

    assert b2["order_id"] == b1["order_id"]
    assert b2["subscription_id"] == b1["subscription_id"]


@pytest.mark.unit
def test_plant_coupon_checkout_idempotency_key_reuse_with_different_payload_conflicts(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    headers = {"Idempotency-Key": "idem-xyz"}
    base = {"coupon_code": "WAOOAW100", "agent_id": "agent-123", "customer_id": "cust-1"}

    r1 = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={**base, "duration": "monthly"},
        headers=headers,
    )
    assert r1.status_code == 200

    r2 = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={**base, "duration": "quarterly"},
        headers=headers,
    )
    assert r2.status_code == 409


@pytest.mark.unit
def test_plant_coupon_checkout_accepts_valid_gstin_and_normalizes(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
            "gstin": "27abcde1234f1z5",
        },
    )
    assert resp.status_code == 200


@pytest.mark.unit
def test_plant_coupon_checkout_rejects_invalid_gstin(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
            "gstin": "NOT-A-GSTIN",
        },
    )
    assert resp.status_code == 400


@pytest.mark.unit
def test_plant_coupon_checkout_idempotency_conflicts_when_gstin_differs(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    headers = {"Idempotency-Key": "idem-gstin"}

    r1 = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
            "gstin": "27ABCDE1234F1Z5",
        },
        headers=headers,
    )
    assert r1.status_code == 200

    r2 = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
            "gstin": "29ABCDE1234F1Z5",
        },
        headers=headers,
    )
    assert r2.status_code == 409
