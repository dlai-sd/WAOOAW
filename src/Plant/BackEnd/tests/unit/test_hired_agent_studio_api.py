from __future__ import annotations

from datetime import datetime, timezone

import pytest


def _create_marketing_hire(test_client, customer_id: str = "cust-1") -> tuple[str, str]:
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
            "nickname": "Growth Copilot",
            "theme": "dark",
            "config": {
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "brand_name": "Acme Health",
                "location": "Pune",
                "offerings_services": ["Dental care"],
                "platforms_enabled": ["youtube"],
                "platform_credentials": {"youtube": "projects/demo/secrets/youtube/versions/latest"},
            },
        },
    )
    assert draft.status_code == 200
    return subscription_id, draft.json()["hired_instance_id"]


@pytest.mark.unit
def test_hired_agent_studio_snapshot_returns_activation_mode_for_incomplete_connection(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)

    response = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "activation"
    assert body["current_step"] in {"connection", "review", "operating_plan"}
    assert any(step["key"] == "connection" and step["complete"] is False for step in body["steps"])


@pytest.mark.unit
def test_hired_agent_studio_snapshot_returns_edit_mode_for_active_hire(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)

    finalize = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={
            "customer_id": "cust-1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "goals_completed": True,
        },
    )
    assert finalize.status_code == 200
    assert finalize.json()["trial_status"] == "active"

    response = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "edit"
    assert body["review"]["summary"] != "Ready to start the trial."
    assert any(step["key"] == "review" for step in body["steps"])


@pytest.mark.unit
def test_hired_agent_studio_snapshot_hides_non_owned_record(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)

    response = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-other"},
    )
    assert response.status_code == 404


@pytest.mark.unit
def test_hired_agent_studio_patch_identity_keeps_edit_mode(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)
    test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={
            "customer_id": "cust-1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "goals_completed": True,
        },
    )

    response = test_client.patch(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-1"},
        json={"identity": {"nickname": "Channel Copilot", "theme": "light"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "edit"
    assert body["identity"]["nickname"] == "Channel Copilot"
    assert body["identity"]["theme"] == "light"


@pytest.mark.unit
def test_hired_agent_studio_patch_operating_plan_preserves_active_trial(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)
    finalize = test_client.post(
        f"/api/v1/hired-agents/{hired_instance_id}/finalize",
        json={
            "customer_id": "cust-1",
            "agent_type_id": "marketing.digital_marketing.v1",
            "goals_completed": True,
        },
    )
    assert finalize.status_code == 200
    assert finalize.json()["trial_status"] == "active"

    response = test_client.patch(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-1"},
        json={
            "operating_plan": {
                "config_patch": {
                    "approval_preferences": {"mode": "manual"}
                }
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "edit"

    by_id = test_client.get(
        f"/api/v1/hired-agents/by-id/{hired_instance_id}",
        params={"customer_id": "cust-1"},
    )
    assert by_id.status_code == 200
    assert by_id.json()["trial_status"] == "active"
    assert by_id.json()["config"]["approval_preferences"]["mode"] == "manual"


@pytest.mark.unit
def test_hired_agent_studio_patch_rejects_read_only_subscription(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    _, hired_instance_id = _create_marketing_hire(test_client)

    from api.v1 import hired_agents_simple

    async def _mock_canceled(*, subscription_id: str, db):
        return "canceled", datetime.now(timezone.utc)

    monkeypatch.setattr(hired_agents_simple, "_subscription_status_and_ended_at", _mock_canceled)

    response = test_client.patch(
        f"/api/v1/hired-agents/{hired_instance_id}/studio",
        params={"customer_id": "cust-1"},
        json={"identity": {"nickname": "Blocked"}},
    )
    assert response.status_code == 409
    assert "read-only" in response.json()["detail"]