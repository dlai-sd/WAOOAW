from __future__ import annotations

import pytest


@pytest.mark.unit
def test_digital_marketing_activation_workspace_persists_and_materializes_marketing_config(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-dma-1"
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-MKT-DMA-001",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-DMA-001",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": customer_id,
            "nickname": "DMA",
            "theme": "dark",
            "config": {},
        },
    )
    hired_instance_id = draft.json()["hired_instance_id"]

    saved = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        json={
            "customer_id": customer_id,
            "workspace": {
                "brand_name": "WAOOAW",
                "location": "Bengaluru",
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "offerings_services": ["SEO", "Content"],
                "platforms_enabled": ["instagram"],
                "platform_bindings": {
                    "instagram": {"credential_id": "cred-ig-1"},
                },
            },
        },
    )

    assert saved.status_code == 200
    body = saved.json()
    assert body["workspace"]["brand_name"] == "WAOOAW"
    assert body["readiness"]["brief_complete"] is True
    assert body["readiness"]["configured"] is True
    assert body["readiness"]["can_finalize"] is True

    resumed = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        params={"customer_id": customer_id},
    )
    assert resumed.status_code == 200
    resumed_body = resumed.json()
    assert resumed_body["workspace"]["platforms_enabled"] == ["instagram"]

    by_id = test_client.get(
        f"/api/v1/hired-agents/by-id/{hired_instance_id}",
        params={"customer_id": customer_id},
    )
    assert by_id.status_code == 200
    config = by_id.json()["config"]
    assert config["digital_marketing_activation"]["brand_name"] == "WAOOAW"
    assert config["platform_credentials"]["instagram"]["credential_ref"] == "cred-ig-1"


@pytest.mark.unit
def test_digital_marketing_activation_requires_youtube_connection_when_selected(test_client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")

    customer_id = "cust-dma-yt-1"
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-MKT-DMA-001",
            "duration": "monthly",
            "customer_id": customer_id,
        },
    )
    subscription_id = checkout.json()["subscription_id"]

    draft = test_client.put(
        "/api/v1/hired-agents/draft",
        json={
            "subscription_id": subscription_id,
            "agent_id": "AGT-MKT-DMA-001",
            "agent_type_id": "marketing.digital_marketing.v1",
            "customer_id": customer_id,
            "nickname": "DMA",
            "theme": "dark",
            "config": {},
        },
    )
    hired_instance_id = draft.json()["hired_instance_id"]

    saved = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        json={
            "customer_id": customer_id,
            "workspace": {
                "brand_name": "WAOOAW",
                "location": "Bengaluru",
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "offerings_services": ["SEO", "Content"],
                "platforms_enabled": ["youtube"],
                "platform_bindings": {
                    "youtube": {"skill_id": "skill-youtube-1"},
                },
            },
        },
    )

    assert saved.status_code == 200
    body = saved.json()
    assert body["readiness"]["brief_complete"] is False
    assert body["readiness"]["youtube_selected"] is True
    assert body["readiness"]["youtube_connection_ready"] is False
    assert "youtube_connection" in body["readiness"]["missing_requirements"]
