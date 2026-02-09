import pytest


@pytest.mark.unit
def test_receipt_created_on_coupon_checkout_and_retrievable(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-rct-1"

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["order_id"]

    listed = test_client.get(f"/api/v1/receipts?customer_id={customer_id}")
    assert listed.status_code == 200
    receipts = listed.json()["receipts"]
    assert any(r["order_id"] == order_id for r in receipts)

    by_order = test_client.get(f"/api/v1/receipts/by-order/{order_id}?customer_id={customer_id}")
    assert by_order.status_code == 200
    receipt = by_order.json()
    assert receipt["order_id"] == order_id
    assert receipt["customer_id"] == customer_id
    assert receipt["receipt_number"].startswith("RCT-")

    html = test_client.get(f"/api/v1/receipts/{receipt['receipt_id']}/html?customer_id={customer_id}")
    assert html.status_code == 200
    assert "Receipt" in html.text
    assert receipt["receipt_number"] in html.text


@pytest.mark.unit
def test_invoice_can_be_disabled_while_receipt_still_exists(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("ISSUE_GST_INVOICE", "false")

    customer_id = "cust-rct-2"

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-xyz",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["order_id"]

    invoices = test_client.get(f"/api/v1/invoices?customer_id={customer_id}").json()["invoices"]
    assert invoices == []

    receipt = test_client.get(f"/api/v1/receipts/by-order/{order_id}?customer_id={customer_id}")
    assert receipt.status_code == 200
    assert receipt.json()["order_id"] == order_id
