import pytest


@pytest.mark.unit
def test_invoice_created_on_coupon_checkout_and_retrievable(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("ISSUE_GST_INVOICE", "true")
    monkeypatch.setenv("SELLER_GSTIN", "27WAOOAW1234F1Z5")

    customer_id = "cust-inv-1"
    customer_gstin = "29ABCDE1234F1Z5"

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": customer_id,
            "gstin": customer_gstin,
        },
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["order_id"]

    listed = test_client.get(f"/api/v1/invoices?customer_id={customer_id}")
    assert listed.status_code == 200
    invoices = listed.json()["invoices"]
    assert any(inv["order_id"] == order_id for inv in invoices)

    by_order = test_client.get(f"/api/v1/invoices/by-order/{order_id}?customer_id={customer_id}")
    assert by_order.status_code == 200
    invoice = by_order.json()
    assert invoice["order_id"] == order_id
    assert invoice["customer_id"] == customer_id
    assert invoice["invoice_number"].startswith("INV-")
    assert invoice["seller_gstin"] == "27WAOOAW1234F1Z5"
    assert invoice["customer_gstin"] == customer_gstin
    assert invoice["tax_type"] == "igst"

    html = test_client.get(f"/api/v1/invoices/{invoice['invoice_id']}/html?customer_id={customer_id}")
    assert html.status_code == 200
    assert "Tax Invoice" in html.text
    assert invoice["invoice_number"] in html.text
