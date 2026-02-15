from __future__ import annotations

import pytest


@pytest.mark.unit
def test_deliverables_generated_reviewed_and_executed(test_client, monkeypatch):
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
                "risk_limits": {"max_units_per_order": 2},
            },
        },
    )
    assert draft.status_code == 200
    hired_instance_id = draft.json()["hired_instance_id"]

    goal = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        json={
            "customer_id": customer_id,
            "goal_template_id": "trading.trade_intent_draft.v1",
            "frequency": "on_demand",
            "settings": {"coin": "BTC", "side": "buy", "units": 1},
        },
    )
    assert goal.status_code == 200

    listed_1 = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
        params={"customer_id": customer_id},
    )
    assert listed_1.status_code == 200
    deliverables_1 = listed_1.json()["deliverables"]
    assert len(deliverables_1) == 1
    deliverable_id = deliverables_1[0]["deliverable_id"]
    assert deliverables_1[0]["review_status"] == "pending_review"
    assert deliverables_1[0]["execution_status"] == "not_executed"

    # Listing again should not create duplicates (Phase-1 simple: one per goal instance).
    listed_2 = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
        params={"customer_id": customer_id},
    )
    assert listed_2.status_code == 200
    deliverables_2 = listed_2.json()["deliverables"]
    assert len(deliverables_2) == 1
    assert deliverables_2[0]["deliverable_id"] == deliverable_id

    reviewed = test_client.post(
        f"/api/v1/deliverables/{deliverable_id}/review",
        json={"customer_id": customer_id, "decision": "approved", "notes": "LGTM"},
    )
    assert reviewed.status_code == 200
    approval_id = reviewed.json()["approval_id"]
    assert approval_id
    assert reviewed.json()["review_status"] == "approved"

    missing_execute = test_client.post(
        f"/api/v1/deliverables/{deliverable_id}/execute",
        json={"customer_id": customer_id},
        headers={"X-Correlation-ID": "cid-missing-1"},
    )
    assert missing_execute.status_code == 403
    missing_body = missing_execute.json()
    assert missing_body["title"] == "Policy Enforcement Denied"
    assert missing_body["reason"] == "approval_required"
    assert missing_body["correlation_id"] == "cid-missing-1"

    wrong_execute = test_client.post(
        f"/api/v1/deliverables/{deliverable_id}/execute",
        json={"customer_id": customer_id, "approval_id": "APR-wrong"},
        headers={"X-Correlation-ID": "cid-wrong-1"},
    )
    assert wrong_execute.status_code == 403
    wrong_body = wrong_execute.json()
    assert wrong_body["title"] == "Policy Enforcement Denied"
    assert wrong_body["reason"] == "approval_invalid"
    assert wrong_body["correlation_id"] == "cid-wrong-1"

    executed = test_client.post(
        f"/api/v1/deliverables/{deliverable_id}/execute",
        json={"customer_id": customer_id, "approval_id": approval_id},
    )
    assert executed.status_code == 200
    assert executed.json()["execution_status"] == "executed"
    assert executed.json()["executed_at"] is not None
