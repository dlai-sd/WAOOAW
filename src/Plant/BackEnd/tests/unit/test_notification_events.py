from __future__ import annotations

import pytest


@pytest.mark.unit
def test_notification_events_emitted_for_payment_and_trial_activation(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    from services import notification_events

    # Ensure store is fresh for this test.
    notification_events.default_notification_event_store.cache_clear()
    store = notification_events.get_notification_event_store()

    customer_id = "cust-notif-1"

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

    payment_events = store.list_records(event_type="payment_success", customer_id=customer_id, limit=20)
    assert any(e.subscription_id == subscription_id for e in payment_events)

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

    trial_events = store.list_records(event_type="trial_activated", customer_id=customer_id, limit=20)
    assert any(e.hired_instance_id == hired_instance_id for e in trial_events)
