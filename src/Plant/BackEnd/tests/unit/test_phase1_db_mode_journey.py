"""DB-mode Phase-1 journey integration tests (PH1-5.1).

Proves register (subscription) -> hire draft -> goals -> finalize, for both agent types.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.v1 import hired_agents_simple
from main import app


pytestmark = pytest.mark.integration


def _unique_customer_id() -> str:
    return f"cust-{uuid4()}"


def _unique_agent_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


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


@pytest.mark.parametrize(
    "agent_type_id,agent_id_prefix,draft_config,goal_template_id,goal_frequency,goal_settings",
    [
        (
            "marketing.digital_marketing.v1",
            "AGT-MKT-TEST",
            {
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "brand_name": "Acme Dental",
                "offerings_services": ["Dental care"],
                "location": "Mumbai",
                "platforms": [
                    {
                        "platform": "instagram",
                        "credential_ref": "CRED-test",
                        "posting_identity": "AcmeDental",
                    }
                ],
            },
            "marketing.weekly_multichannel_batch.v1",
            "weekly",
            {"topics": ["oral health"]},
        ),
        (
            "trading.share_trader.v1",
            "AGT-TRD-TEST",
            {
                "timezone": "Asia/Kolkata",
                "exchange_provider": "delta_exchange_india",
                "exchange_credential_ref": "EXCH-test",
                "allowed_coins": ["BTC"],
                "default_coin": "BTC",
                "interval_seconds": 300,
                "risk_limits": {"max_units_per_order": 1},
            },
            "trading.trade_intent_draft.v1",
            "on_demand",
            {"coin": "BTC", "side": "buy", "units": 1},
        ),
    ],
)
def test_phase1_db_mode_register_hire_finalize_journey(
    migrated_db,
    monkeypatch,
    agent_type_id: str,
    agent_id_prefix: str,
    draft_config: dict,
    goal_template_id: str,
    goal_frequency: str,
    goal_settings: dict,
):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")

    customer_id = _unique_customer_id()
    agent_id = _unique_agent_id(agent_id_prefix)

    with TestClient(app) as client:
        subscription_id = _coupon_checkout(client, customer_id=customer_id, agent_id=agent_id)

        drafted = client.put(
            "/api/v1/hired-agents/draft",
            json={
                "subscription_id": subscription_id,
                "agent_id": agent_id,
                "agent_type_id": agent_type_id,
                "customer_id": customer_id,
                "nickname": "Agent",
                "theme": "dark",
                "config": draft_config,
            },
        )
        assert drafted.status_code == 200
        hired_instance_id = str(drafted.json()["hired_instance_id"])

        goal_upsert = client.put(
            f"/api/v1/hired-agents/{hired_instance_id}/goals",
            json={
                "customer_id": customer_id,
                "goal_template_id": goal_template_id,
                "frequency": goal_frequency,
                "settings": goal_settings,
            },
        )
        assert goal_upsert.status_code == 200
        goal_instance_id = str(goal_upsert.json()["goal_instance_id"])

        finalized = client.post(
            f"/api/v1/hired-agents/{hired_instance_id}/finalize",
            json={
                "customer_id": customer_id,
                "agent_type_id": agent_type_id,
                "goals_completed": True,
            },
        )
        assert finalized.status_code == 200
        assert finalized.json()["trial_status"] == "active"

        # Prove DB is the source of truth by clearing in-memory maps.
        hired_agents_simple._by_id.clear()
        hired_agents_simple._by_subscription.clear()
        hired_agents_simple._goals_by_hired_instance.clear()

        fetched = client.get(
            f"/api/v1/hired-agents/by-subscription/{subscription_id}",
            params={"customer_id": customer_id},
        )
        assert fetched.status_code == 200
        assert fetched.json()["hired_instance_id"] == hired_instance_id

        fetched_goals = client.get(
            f"/api/v1/hired-agents/{hired_instance_id}/goals",
            params={"customer_id": customer_id},
        )
        assert fetched_goals.status_code == 200
        goal_ids = [g["goal_instance_id"] for g in fetched_goals.json()["goals"]]
        assert goal_instance_id in goal_ids


def test_db_mode_does_not_fall_back_to_in_memory_maps(migrated_db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")

    customer_id = _unique_customer_id()
    agent_id = _unique_agent_id("AGT-TRD-TEST")

    with TestClient(app) as client:
        subscription_id = _coupon_checkout(client, customer_id=customer_id, agent_id=agent_id)

        drafted = client.put(
            "/api/v1/hired-agents/draft",
            json={
                "subscription_id": subscription_id,
                "agent_id": agent_id,
                "agent_type_id": "trading.share_trader.v1",
                "customer_id": customer_id,
                "nickname": "Agent",
                "theme": "dark",
                "config": {
                    "timezone": "Asia/Kolkata",
                    "exchange_provider": "delta_exchange_india",
                    "exchange_credential_ref": "EXCH-test",
                    "allowed_coins": ["BTC"],
                    "default_coin": "BTC",
                    "interval_seconds": 300,
                    "risk_limits": {"max_units_per_order": 1},
                },
            },
        )
        assert drafted.status_code == 200

        # Seed misleading in-memory state that would break memory-mode reads.
        hired_agents_simple._by_id.clear()
        hired_agents_simple._by_subscription.clear()
        hired_agents_simple._by_subscription[subscription_id] = "HAI-BAD"

        fetched = client.get(
            f"/api/v1/hired-agents/by-subscription/{subscription_id}",
            params={"customer_id": customer_id},
        )
        assert fetched.status_code == 200
