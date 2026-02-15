from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.unit
def test_goal_scheduler_runs_due_goals_idempotently(test_client, monkeypatch):
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

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-HEALTH-001",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": customer_id,
            "nickname": "Marketer",
            "theme": "dark",
            "config": {
                "primary_language": "en",
                "timezone": "UTC",
                "brand_name": "Cake Shop",
                "location": "Pune",
                "offerings_services": ["Cupcakes"],
                "platforms_enabled": ["instagram"],
                "platform_credentials": {"instagram": {"credential_ref": "CRED-1"}},
            },
        },
    )
    assert draft.status_code == 200
    hired_instance_id = draft.json()["hired_instance_id"]

    goal = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/goals",
        json={
            "customer_id": customer_id,
            "goal_template_id": "marketing.daily_micro_post.v1",
            "frequency": "daily",
            "settings": {"topic": "Heart health"},
        },
    )
    assert goal.status_code == 200

    finalized = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={"customer_id": customer_id, "agent_type_id": "marketing.digital_marketing.v1", "goals_completed": True},
    )
    assert finalized.status_code == 200

    day1 = datetime(2026, 2, 10, 1, 0, 0, tzinfo=timezone.utc)
    run1 = test_client.post(
        "/api/v1/scheduler/goals/run-due",
        json={"now": day1.isoformat(), "hired_instance_id": hired_instance_id},
    )
    assert run1.status_code == 200
    assert run1.json()["generated"] == 1

    # Re-running in the same period is idempotent.
    run1b = test_client.post(
        "/api/v1/scheduler/goals/run-due",
        json={"now": day1.isoformat(), "hired_instance_id": hired_instance_id},
    )
    assert run1b.status_code == 200
    assert run1b.json()["generated"] == 0

    listed_day1 = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
        params={"customer_id": customer_id, "as_of": day1.isoformat()},
    )
    assert listed_day1.status_code == 200
    assert len(listed_day1.json()["deliverables"]) == 1

    # Next day should create a new draft.
    day2 = day1 + timedelta(days=1)
    run2 = test_client.post(
        "/api/v1/scheduler/goals/run-due",
        json={"now": day2.isoformat(), "hired_instance_id": hired_instance_id},
    )
    assert run2.status_code == 200
    assert run2.json()["generated"] == 1

    listed_day2 = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
        params={"customer_id": customer_id, "as_of": day2.isoformat()},
    )
    assert listed_day2.status_code == 200
    assert len(listed_day2.json()["deliverables"]) == 2
