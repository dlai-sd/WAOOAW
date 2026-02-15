from __future__ import annotations

import pytest


@pytest.mark.unit
def test_goals_crud_and_validation_against_templates(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-1"
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-TRD-DELTA-001",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-TRD-DELTA-001",
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
                "interval_seconds": 60,
                "risk_limits": {"max_units_per_order": 1},
            },
        },
    )
    assert draft.status_code == 200
    hired_instance_id = draft.json()["hired_instance_id"]

    # Missing required settings for trading.trade_intent_draft.v1 should be rejected.
    bad_goal = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        json={
            "customer_id": customer_id,
            "goal_template_id": "trading.trade_intent_draft.v1",
            "frequency": "on_demand",
            "settings": {"coin": "BTC"},
        },
    )
    assert bad_goal.status_code == 400

    created = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        json={
            "customer_id": customer_id,
            "goal_template_id": "trading.trade_intent_draft.v1",
            "frequency": "on_demand",
            "settings": {"coin": "BTC", "side": "buy", "units": 1},
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["hired_instance_id"] == hired_instance_id
    assert body["goal_template_id"] == "trading.trade_intent_draft.v1"
    assert body["frequency"] == "on_demand"
    assert body["settings"]["coin"] == "BTC"

    listed = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        params={"customer_id": customer_id},
    )
    assert listed.status_code == 200
    goals = listed.json()["goals"]
    assert len(goals) == 1
    goal_instance_id = goals[0]["goal_instance_id"]

    updated = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        json={
            "customer_id": customer_id,
            "goal_instance_id": goal_instance_id,
            "goal_template_id": "trading.trade_intent_draft.v1",
            "frequency": "on_demand",
            "settings": {"coin": "BTC", "side": "sell", "units": 2},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["goal_instance_id"] == goal_instance_id
    assert updated.json()["settings"]["side"] == "sell"

    deleted = test_client.delete(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        params={"customer_id": customer_id, "goal_instance_id": goal_instance_id},
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    listed_again = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        params={"customer_id": customer_id},
    )
    assert listed_again.status_code == 200
    assert listed_again.json()["goals"] == []
