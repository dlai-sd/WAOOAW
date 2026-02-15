from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.unit
def test_cancel_at_period_end_sets_flag_and_keeps_active(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    cancel = test_client.post(
        f"/api/v1/payments/subscriptions/{subscription_id}/cancel",
        params={"customer_id": "cust-1"},
    )
    assert cancel.status_code == 200
    body = cancel.json()
    assert body["subscription_id"] == subscription_id
    assert body["status"] == "active"
    assert body["cancel_at_period_end"] is True


@pytest.mark.unit
def test_process_period_end_cancels_and_deactivates_hired_agent(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    from services import notification_events

    notification_events.default_notification_event_store.cache_clear()
    store = notification_events.get_notification_event_store()

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": "cust-1",
            "nickname": "My Agent",
            "theme": "dark",
        },
    )
    assert draft.status_code == 200
    assert draft.json()["active"] is True

    cancel = test_client.post(
        f"/api/v1/payments/subscriptions/{subscription_id}/cancel",
        params={"customer_id": "cust-1"},
    )
    assert cancel.status_code == 200

    # Move time beyond period end and process.
    now = datetime.now(timezone.utc) + timedelta(days=60)
    processed = test_client.post(
        "/api/v1/payments/subscriptions/process-period-end",
        json={"now": now.isoformat()},
    )
    assert processed.status_code == 200
    assert processed.json()["processed"] >= 1

    sub = test_client.get(f"/api/v1/payments/subscriptions/{subscription_id}")
    assert sub.status_code == 200
    assert sub.json()["status"] == "canceled"
    assert sub.json().get("ended_at")

    resumed = test_client.get(f"/api/v1/hired-agents/by-subscription/{subscription_id}?customer_id=cust-1")
    assert resumed.status_code == 200
    resumed_body = resumed.json()
    assert resumed_body["active"] is False

    deactivated = store.list_records(event_type="hired_agent_deactivated", customer_id="cust-1", limit=50)
    assert any(
        e.subscription_id == subscription_id and e.hired_instance_id == resumed_body["hired_instance_id"]
        for e in deactivated
    )

    # Retention enforcement: after cancel is effective, the instance is read-only.
    rejected_draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": "cust-1",
            "nickname": "Should Fail",
            "theme": "dark",
        },
    )
    assert rejected_draft.status_code == 409

    rejected_finalize = test_client.post(
        f"/api/v1/hired-agents/{resumed_body['hired_instance_id']}/finalize",
        json={"customer_id": "cust-1", "agent_type_id": "marketing.digital_marketing.v1", "goals_completed": True},
    )
    assert rejected_finalize.status_code == 409


@pytest.mark.unit
def test_retention_policy_expires_hired_agent_read_access(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("END_RETENTION_DAYS", "1")

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "cust-1",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": "cust-1",
            "nickname": "My Agent",
            "theme": "dark",
        },
    )
    assert draft.status_code == 200

    cancel = test_client.post(
        f"/api/v1/payments/subscriptions/{subscription_id}/cancel",
        params={"customer_id": "cust-1"},
    )
    assert cancel.status_code == 200

    # Move time beyond period end and process.
    ended_at = datetime.now(timezone.utc) + timedelta(days=60)
    processed = test_client.post(
        "/api/v1/payments/subscriptions/process-period-end",
        json={"now": ended_at.isoformat()},
    )
    assert processed.status_code == 200
    assert processed.json()["processed"] >= 1

    # Within retention window, read still succeeds.
    within = test_client.get(
        f"/api/v1/hired-agents/by-subscription/{subscription_id}",
        params={"as_of": (ended_at + timedelta(hours=12)).isoformat(), "customer_id": "cust-1"},
    )
    assert within.status_code == 200
    within_body = within.json()
    assert within_body.get("subscription_ended_at")
    assert within_body.get("retention_expires_at")

    # Past retention window, read is gone (410).
    expired = test_client.get(
        f"/api/v1/hired-agents/by-subscription/{subscription_id}",
        params={"as_of": (ended_at + timedelta(days=2)).isoformat(), "customer_id": "cust-1"},
    )
    assert expired.status_code == 410
