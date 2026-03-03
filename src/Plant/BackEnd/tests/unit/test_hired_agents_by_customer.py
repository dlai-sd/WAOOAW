"""Unit tests for GET /api/v1/hired-agents/by-customer/{customer_id}.

E1-S1 of CP-MY-AGENTS-1: covers memory-mode and DB-fallback behaviour.
Tests run in memory mode (PERSISTENCE_MODE defaults to "db" but test fixtures
use the in-memory path when no DB session is available).
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_by_customer_unknown_returns_empty(test_client, monkeypatch):
    """Unknown customer_id returns 200 with empty instances — never 404."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    resp = test_client.get("/api/v1/hired-agents/by-customer/unknown-customer-xyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == "unknown-customer-xyz"
    assert body["instances"] == []


@pytest.mark.unit
def test_by_customer_blank_id_returns_empty(test_client, monkeypatch):
    """Blank/whitespace customer_id returns 200 with empty instances."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    resp = test_client.get("/api/v1/hired-agents/by-customer/   ")
    assert resp.status_code == 200
    body = resp.json()
    assert body["instances"] == []


@pytest.mark.unit
def test_by_customer_returns_seeded_in_memory_agents(test_client, monkeypatch):
    """After creating a hired agent via PUT /draft, by-customer returns it."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    # Create a subscription first.
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-MKT-001",
            "duration": "monthly",
            "customer_id": "cust-test-by-customer-01",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    # Upsert a draft hired agent.
    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-001",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": "cust-test-by-customer-01",
            "nickname": "Content Creator",
        },
    )
    assert draft.status_code == 200

    # by-customer should now find it.
    resp = test_client.get("/api/v1/hired-agents/by-customer/cust-test-by-customer-01")
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == "cust-test-by-customer-01"
    assert len(body["instances"]) >= 1
    found = next(
        (i for i in body["instances"] if i["subscription_id"] == subscription_id), None
    )
    assert found is not None
    assert found["agent_id"] == "AGT-MKT-001"
    assert found["agent_type_id"] == "marketing.digital_marketing.v1"
    assert found["nickname"] == "Content Creator"


@pytest.mark.unit
def test_by_customer_does_not_return_other_customers_agents(test_client, monkeypatch):
    """Agents belonging to a different customer are not returned."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-TRD-001",
            "duration": "monthly",
            "customer_id": "cust-owner-99",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-TRD-001",
            "agent_type_id": "trading.share_trader.v1",
            "customer_id": "cust-owner-99",
            "nickname": "Share Trader 99",
        },
    )

    # Query a different customer — should get empty list.
    resp = test_client.get("/api/v1/hired-agents/by-customer/cust-other-99")
    assert resp.status_code == 200
    body = resp.json()
    assert not any(i["subscription_id"] == subscription_id for i in body["instances"])
