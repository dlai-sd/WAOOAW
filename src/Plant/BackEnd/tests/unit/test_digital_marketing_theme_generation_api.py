from __future__ import annotations

import json

import pytest

import api.v1.campaigns as campaigns_module


def _create_marketing_hire(test_client, customer_id: str = "cust-dma") -> str:
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
                "platforms_enabled": ["youtube", "instagram"],
            },
        },
    )
    assert draft.status_code == 200
    return draft.json()["hired_instance_id"]


@pytest.mark.unit
def test_generate_theme_plan_persists_master_and_three_derived_themes(test_client, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client)

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps(
            {
                "master_theme": "Own your local market with educational trust content",
                "derived_themes": [
                    {"title": "Problem awareness", "description": "Explain the pain points", "frequency": "weekly"},
                    {"title": "Treatment proof", "description": "Show before/after outcomes", "frequency": "weekly"},
                    {"title": "Clinic credibility", "description": "Highlight expertise and reviews", "frequency": "weekly"},
                ],
            }
        ),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "schedule": {
                    "start_date": "2026-03-22",
                    "posts_per_week": 3,
                    "preferred_days": ["mon", "wed", "fri"],
                    "preferred_hours_utc": [9, 17],
                }
            }
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["master_theme"] == "Own your local market with educational trust content"
    assert len(body["derived_themes"]) == 3

    campaign_ids = [
        campaign_id
        for campaign_id, campaign in campaigns_module._campaigns.items()
        if campaign.hired_instance_id == hired_instance_id
    ]
    assert len(campaign_ids) == 1
    assert len(campaigns_module._theme_items[campaign_ids[0]]) == 3


@pytest.mark.unit
def test_generate_theme_plan_reuses_existing_draft_campaign(test_client, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-dma-2")

    import api.v1.digital_marketing_activation as dma_module

    responses = iter(
        [
            json.dumps(
                {
                    "master_theme": "Trust-first launch",
                    "derived_themes": [{"title": "Week 1", "description": "First theme", "frequency": "weekly"}],
                }
            ),
            json.dumps(
                {
                    "master_theme": "Trust-first launch updated",
                    "derived_themes": [{"title": "Week 2", "description": "Second theme", "frequency": "weekly"}],
                }
            ),
        ]
    )
    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(dma_module, "grok_complete", lambda *args, **kwargs: next(responses))

    first = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={"campaign_setup": {"schedule": {"start_date": "2026-03-22", "posts_per_week": 2}}},
    )
    second = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={"campaign_setup": {"schedule": {"start_date": "2026-03-22", "posts_per_week": 2}}},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["campaign_id"] == second.json()["campaign_id"]
