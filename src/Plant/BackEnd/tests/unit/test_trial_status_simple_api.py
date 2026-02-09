import pytest


@pytest.mark.unit
def test_trial_status_by_subscription_and_list(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-trial-1"

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
            "nickname": "My Agent",
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

    by_sub = test_client.get(f"/api/v1/trial-status/by-subscription/{subscription_id}?customer_id={customer_id}")
    assert by_sub.status_code == 200
    body = by_sub.json()
    assert body["subscription_id"] == subscription_id
    assert body["trial_status"] == "active"
    assert body["trial_start_at"]
    assert body["trial_end_at"]

    listed = test_client.get(f"/api/v1/trial-status?customer_id={customer_id}")
    assert listed.status_code == 200
    trials = listed.json()["trials"]
    assert any(t["subscription_id"] == subscription_id for t in trials)


@pytest.mark.unit
def test_trial_status_customer_scoped(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-xyz",
            "duration": "monthly",
            "customer_id": "cust-a",
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    # Create hired agent instance bound to cust-a
    test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-xyz",
            "customer_id": "cust-a",
            "nickname": "A",
            "theme": "dark",
        },
    )

    # Wrong customer_id should not see anything
    res = test_client.get(f"/api/v1/trial-status/by-subscription/{subscription_id}?customer_id=cust-b")
    assert res.status_code == 404
