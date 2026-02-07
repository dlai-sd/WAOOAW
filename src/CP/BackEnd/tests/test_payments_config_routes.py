import pytest


@pytest.mark.unit
def test_payments_config_defaults_to_coupon_in_dev(client, monkeypatch):
    monkeypatch.delenv("PAYMENTS_MODE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    resp = client.get("/api/cp/payments/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "coupon"
    assert body["coupon_code"] == "WAOOAW100"
    assert body["coupon_unlimited"] is True


@pytest.mark.unit
def test_payments_config_defaults_to_razorpay_in_prod(client, monkeypatch):
    monkeypatch.delenv("PAYMENTS_MODE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    resp = client.get("/api/cp/payments/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "razorpay"
    assert body.get("coupon_code") is None


@pytest.mark.unit
def test_payments_config_rejects_coupon_mode_in_prod(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    resp = client.get("/api/cp/payments/config")
    assert resp.status_code == 500
    assert "not allowed" in resp.text.lower()


@pytest.mark.unit
def test_payments_config_rejects_invalid_mode(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "nope")

    resp = client.get("/api/cp/payments/config")
    assert resp.status_code == 500
    assert "invalid payments_mode" in resp.text.lower()
