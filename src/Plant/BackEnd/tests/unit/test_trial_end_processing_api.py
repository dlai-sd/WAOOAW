from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.unit
def test_process_trial_end_auto_converts_when_subscription_active(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-1"
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
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "customer_id": customer_id,
            "nickname": "N",
            "theme": "dark",
        },
    )
    assert draft.status_code == 200
    hired_instance_id = draft.json()["hired_instance_id"]

    finalize = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize.status_code == 200
    assert finalize.json()["trial_status"] == "active"

    now = datetime.now(timezone.utc) + timedelta(days=10)
    processed = test_client.post(
        "/api/v1/hired-agents/process-trial-end",
        json={"now": now.isoformat()},
    )
    assert processed.status_code == 200
    assert processed.json()["processed"] >= 1

    resumed = test_client.get(f"/api/v1/hired-agents/by-subscription/{subscription_id}?customer_id={customer_id}")
    assert resumed.status_code == 200
    assert resumed.json()["trial_status"] == "ended_converted"

    # Idempotent: rerun should not re-process.
    processed_again = test_client.post(
        "/api/v1/hired-agents/process-trial-end",
        json={"now": (now + timedelta(days=1)).isoformat()},
    )
    assert processed_again.status_code == 200
    assert processed_again.json()["processed"] == 0
