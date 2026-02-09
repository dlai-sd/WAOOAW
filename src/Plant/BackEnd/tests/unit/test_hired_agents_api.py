from __future__ import annotations

import pytest


@pytest.mark.unit
def test_hired_agent_draft_and_resume_by_subscription(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={"coupon_code": "WAOOAW100", "agent_id": "agent-123", "duration": "monthly", "customer_id": "cust-1"},
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "customer_id": "cust-1",
            "nickname": "My Agent",
            "theme": "dark",
            "config": {"foo": "bar"},
        },
    )
    assert draft.status_code == 200
    body = draft.json()
    assert body["subscription_id"] == subscription_id
    assert body["agent_id"] == "agent-123"
    assert body["nickname"] == "My Agent"
    assert body["theme"] == "dark"
    assert body["configured"] is True
    assert body["trial_status"] == "not_started"

    resumed = test_client.get(f"/api/v1/hired-agents/by-subscription/{subscription_id}?customer_id=cust-1")
    assert resumed.status_code == 200
    resumed_body = resumed.json()
    assert resumed_body["hired_instance_id"] == body["hired_instance_id"]
    assert resumed_body["config"]["foo"] == "bar"


@pytest.mark.unit
def test_finalize_does_not_start_trial_without_goals_completed(test_client, monkeypatch):
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
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "agent-123",
            "customer_id": customer_id,
            "nickname": "N",
            "theme": "default",
        },
    )
    hired_instance_id = draft.json()["hired_instance_id"]

    finalize = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": False},
    )
    assert finalize.status_code == 200
    body = finalize.json()
    assert body["configured"] is True
    assert body["goals_completed"] is False
    assert body["trial_status"] == "not_started"
    assert body["trial_start_at"] is None


@pytest.mark.unit
def test_finalize_starts_trial_when_subscription_active_and_goals_completed(test_client, monkeypatch):
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
    hired_instance_id = draft.json()["hired_instance_id"]

    finalize = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize.status_code == 200
    body = finalize.json()
    assert body["configured"] is True
    assert body["goals_completed"] is True
    assert body["subscription_status"] == "active"
    assert body["trial_status"] == "active"
    assert body["trial_start_at"]
    assert body["trial_end_at"]


@pytest.mark.unit
def test_trading_agent_requires_config_to_be_configured_and_start_trial(test_client, monkeypatch):
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

    draft_incomplete = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-TRD-DELTA-001",
            "customer_id": customer_id,
            "nickname": "Trader",
            "theme": "dark",
            "config": {},
        },
    )
    assert draft_incomplete.status_code == 200
    assert draft_incomplete.json()["configured"] is False

    hired_instance_id = draft_incomplete.json()["hired_instance_id"]
    finalize_should_not_start = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize_should_not_start.status_code == 200
    assert finalize_should_not_start.json()["trial_status"] == "not_started"

    draft_complete = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-TRD-DELTA-001",
            "customer_id": customer_id,
            "nickname": "Trader",
            "theme": "dark",
            "config": {
                "exchange_provider": "delta_exchange_india",
                "exchange_credential_ref": "EXCH-test",
                "allowed_coins": ["BTC"],
                "interval_seconds": 300,
            },
        },
    )
    assert draft_complete.status_code == 200
    assert draft_complete.json()["configured"] is True

    finalize_should_start = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize_should_start.status_code == 200
    assert finalize_should_start.json()["trial_status"] == "active"


@pytest.mark.unit
def test_marketing_agent_requires_platform_credentials_to_be_configured_and_start_trial(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-1"
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-MKT-HEALTH-001",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    assert checkout.status_code == 200
    subscription_id = checkout.json()["subscription_id"]

    draft_incomplete = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": customer_id,
            "nickname": "Marketer",
            "theme": "dark",
            "config": {},
        },
    )
    assert draft_incomplete.status_code == 200
    assert draft_incomplete.json()["configured"] is False

    hired_instance_id = draft_incomplete.json()["hired_instance_id"]
    finalize_should_not_start = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize_should_not_start.status_code == 200
    assert finalize_should_not_start.json()["trial_status"] == "not_started"

    draft_complete = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": customer_id,
            "nickname": "Marketer",
            "theme": "dark",
            "config": {
                "platforms": [
                    {
                        "platform": "instagram",
                        "credential_ref": "CRED-test",
                        "posting_identity": "DrSharmaClinic",
                    }
                ]
            },
        },
    )
    assert draft_complete.status_code == 200
    assert draft_complete.json()["configured"] is True

    finalize_should_start = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "goals_completed": True},
    )
    assert finalize_should_start.status_code == 200
    assert finalize_should_start.json()["trial_status"] == "active"
