import hashlib
import hmac
import json

import pytest


def _checkout_signature(*, secret: str, razorpay_order_id: str, razorpay_payment_id: str) -> str:
    msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def _webhook_signature(*, secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


@pytest.mark.unit
def test_plant_razorpay_order_disabled_when_not_razorpay_mode(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = test_client.post(
        "/api/v1/payments/razorpay/order",
        json={"agent_id": "agent-123", "duration": "monthly"},
    )
    assert resp.status_code == 403


@pytest.mark.unit
def test_plant_razorpay_order_creates_order_and_subscription(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")

    from api.v1 import payments_simple

    async def _fake_create_order(*, amount_in_paise: int, currency: str, receipt: str):
        assert amount_in_paise > 0
        assert currency == "INR"
        assert receipt.startswith("ORDER-")
        return {"id": "order_test_1"}

    monkeypatch.setattr(payments_simple, "_razorpay_create_order", _fake_create_order)

    resp = test_client.post(
        "/api/v1/payments/razorpay/order",
        json={"agent_id": "agent-123", "duration": "monthly"},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["payment_provider"] == "razorpay"
    assert body["currency"] == "INR"
    assert body["amount"] == 12000

    assert body["order_id"].startswith("ORDER-")
    assert body["subscription_id"].startswith("SUB-")

    assert body["razorpay_key_id"] == "rzp_test_key"
    assert body["razorpay_order_id"] == "order_test_1"


@pytest.mark.unit
def test_plant_razorpay_confirm_rejects_invalid_signature(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")

    from api.v1 import payments_simple

    async def _fake_create_order(*, amount_in_paise: int, currency: str, receipt: str):
        return {"id": "order_test_2"}

    monkeypatch.setattr(payments_simple, "_razorpay_create_order", _fake_create_order)

    from services import notification_events

    notification_events.default_notification_event_store.cache_clear()
    store = notification_events.get_notification_event_store()

    create = test_client.post(
        "/api/v1/payments/razorpay/order",
        json={"agent_id": "agent-123", "duration": "monthly"},
    )
    assert create.status_code == 200
    created = create.json()

    resp = test_client.post(
        "/api/v1/payments/razorpay/confirm",
        json={
            "order_id": created["order_id"],
            "razorpay_order_id": created["razorpay_order_id"],
            "razorpay_payment_id": "pay_test_1",
            "razorpay_signature": "bad",
        },
    )
    assert resp.status_code == 400

    failed = store.list_records(event_type="payment_failed", customer_id=None, limit=50)
    assert any(e.order_id == created["order_id"] for e in failed)


@pytest.mark.unit
def test_plant_razorpay_confirm_accepts_valid_signature_and_is_idempotent(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")

    from api.v1 import payments_simple

    async def _fake_create_order(*, amount_in_paise: int, currency: str, receipt: str):
        return {"id": "order_test_3"}

    monkeypatch.setattr(payments_simple, "_razorpay_create_order", _fake_create_order)

    create = test_client.post(
        "/api/v1/payments/razorpay/order",
        json={"agent_id": "agent-123", "duration": "monthly"},
    )
    assert create.status_code == 200
    created = create.json()

    payment_id = "pay_test_2"
    signature = _checkout_signature(
        secret="rzp_test_secret",
        razorpay_order_id=created["razorpay_order_id"],
        razorpay_payment_id=payment_id,
    )

    r1 = test_client.post(
        "/api/v1/payments/razorpay/confirm",
        json={
            "order_id": created["order_id"],
            "razorpay_order_id": created["razorpay_order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["subscription_status"] == "active"
    assert b1["subscription_id"].startswith("SUB-")

    r2 = test_client.post(
        "/api/v1/payments/razorpay/confirm",
        json={
            "order_id": created["order_id"],
            "razorpay_order_id": created["razorpay_order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["subscription_status"] == "active"
    assert b2["subscription_id"] == b1["subscription_id"]


@pytest.mark.unit
def test_plant_razorpay_webhook_rejects_invalid_signature(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test")

    resp = test_client.post(
        "/api/v1/payments/razorpay/webhook",
        data=b"{}",
        headers={"X-Razorpay-Signature": "bad"},
    )
    assert resp.status_code == 400


@pytest.mark.unit
def test_plant_razorpay_webhook_marks_order_paid(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test")

    from api.v1 import payments_simple

    async def _fake_create_order(*, amount_in_paise: int, currency: str, receipt: str):
        return {"id": "order_test_4"}

    monkeypatch.setattr(payments_simple, "_razorpay_create_order", _fake_create_order)

    create = test_client.post(
        "/api/v1/payments/razorpay/order",
        json={"agent_id": "agent-123", "duration": "monthly"},
    )
    assert create.status_code == 200
    created = create.json()

    payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"order_id": created["razorpay_order_id"]}}},
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = _webhook_signature(secret="whsec_test", raw=raw)

    wh = test_client.post(
        "/api/v1/payments/razorpay/webhook",
        data=raw,
        headers={"X-Razorpay-Signature": sig},
    )
    assert wh.status_code == 200
    assert wh.json().get("ok") is True

    # Confirm should now be idempotent success (order already marked paid).
    payment_id = "pay_test_3"
    signature = _checkout_signature(
        secret="rzp_test_secret",
        razorpay_order_id=created["razorpay_order_id"],
        razorpay_payment_id=payment_id,
    )

    r = test_client.post(
        "/api/v1/payments/razorpay/confirm",
        json={
            "order_id": created["order_id"],
            "razorpay_order_id": created["razorpay_order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert r.status_code == 200
    assert r.json()["subscription_status"] == "active"
