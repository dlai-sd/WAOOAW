"""Integration tests covering DB-mode hire API guards (PH1-3.3+).

These tests require a Postgres test database.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


pytestmark = pytest.mark.integration


def _unique_customer_id() -> str:
    return f"cust-{uuid4()}"


def _unique_agent_id() -> str:
    return f"AGT-TRD-DELTA-{uuid4()}"


def _coupon_checkout(client: TestClient, *, customer_id: str, agent_id: str) -> str:
    checkout = client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": agent_id,
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    assert checkout.status_code == 200
    return str(checkout.json()["subscription_id"])


def test_db_mode_rejects_raw_secrets_in_config(migrated_db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")

    customer_id = _unique_customer_id()
    agent_id = _unique_agent_id()

    with TestClient(app) as client:
        subscription_id = _coupon_checkout(client, customer_id=customer_id, agent_id=agent_id)

        rejected = client.put(
            "/api/v1/hired-agents/draft",
            json={
                "subscription_id": subscription_id,
                "agent_id": agent_id,
                "agent_type_id": "trading.share_trader.v1",
                "customer_id": customer_id,
                "nickname": "Trader",
                "theme": "dark",
                "config": {
                    "timezone": "Asia/Kolkata",
                    "exchange_provider": "delta_exchange_india",
                    "exchange_credential_ref": "EXCH-test",
                    "allowed_coins": ["BTC"],
                    "default_coin": "BTC",
                    "interval_seconds": 300,
                    "risk_limits": {"max_units_per_order": 1},
                    "api_key": "SHOULD-NOT-BE-HERE",
                },
            },
        )

        assert rejected.status_code == 400


def test_db_mode_hides_hired_instance_on_customer_mismatch(migrated_db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")

    customer_id = _unique_customer_id()
    other_customer_id = _unique_customer_id()
    agent_id = _unique_agent_id()

    with TestClient(app) as client:
        subscription_id = _coupon_checkout(client, customer_id=customer_id, agent_id=agent_id)

        drafted = client.put(
            "/api/v1/hired-agents/draft",
            json={
                "subscription_id": subscription_id,
                "agent_id": agent_id,
                "agent_type_id": "trading.share_trader.v1",
                "customer_id": customer_id,
                "nickname": "Trader",
                "theme": "dark",
                "config": {},
            },
        )
        assert drafted.status_code == 200

        hidden = client.get(
            f"/api/v1/hired-agents/by-subscription/{subscription_id}",
            params={"customer_id": other_customer_id},
        )
        assert hidden.status_code == 404
