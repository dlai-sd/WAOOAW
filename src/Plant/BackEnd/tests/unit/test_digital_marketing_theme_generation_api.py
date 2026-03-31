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


@pytest.mark.unit
def test_generate_theme_plan_persists_strategy_workshop_state(test_client, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-dma-workshop")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps(
            {
                "assistant_message": "Your clinic should win trust by making treatment decisions feel simple, local, and evidence-backed.",
                "checkpoint_summary": "We have locked the target patient mindset, the trust angle, and the opening content lane.",
                "current_focus_question": "Do we want the first series to focus more on fear reduction or treatment clarity?",
                "next_step_options": ["Refine the audience", "Approve this direction", "Suggest 3 opening content angles"],
                "time_saving_note": "I am reducing this to the one remaining decision so we can finalize quickly.",
                "status": "approval_ready",
                "follow_up_questions": [],
                "summary": {
                    "profession_name": "Doctor",
                    "location_focus": "Pune",
                    "customer_profile": "Families and working professionals delaying treatment.",
                    "service_focus": "Dental care and preventive treatment.",
                    "signature_differentiator": "Calm clinical guidance with strong local trust signals.",
                    "business_goal": "Drive consultation bookings.",
                    "first_content_direction": "Short myth-busting educational videos.",
                    "business_focus": "Dentistry for families and working professionals.",
                    "audience": "Parents and professionals who delay treatment until pain becomes urgent.",
                    "positioning": "The calm, expert local clinic that explains options clearly.",
                    "tone": "Reassuring, clear, and credible.",
                    "content_pillars": ["Pain-to-prevention education", "Proof and outcomes", "Local trust builders"],
                    "youtube_angle": "Turn common treatment fears into practical, confident next steps.",
                    "cta": "Book a consultation before a small issue becomes expensive.",
                },
                "master_theme": "Own your local market with calm, authority-building dental education.",
                "derived_themes": [
                    {"title": "Pain-to-prevention", "description": "Answer urgent symptom questions.", "frequency": "weekly"},
                    {"title": "Treatment clarity", "description": "Explain procedures and outcomes.", "frequency": "weekly"},
                ],
            }
        ),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "status": "discovery",
                    "messages": [
                        {"role": "assistant", "content": "Tell me the business outcome this YouTube channel must create first."}
                    ],
                    "pending_input": "We want more high-intent consultation leads from local families.",
                }
            }
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    workshop = body["workspace"]["campaign_setup"]["strategy_workshop"]
    assert workshop["status"] == "approval_ready"
    assert workshop["summary"]["tone"] == "Reassuring, clear, and credible."
    assert workshop["summary"]["profession_name"] == "Doctor"
    assert workshop["current_focus_question"] == "Do we want the first series to focus more on fear reduction or treatment clarity?"
    assert workshop["next_step_options"][1] == "Approve this direction"
    assert workshop["messages"][-2]["role"] == "user"
    assert workshop["messages"][-2]["content"] == "We want more high-intent consultation leads from local families."
    assert workshop["messages"][-1]["role"] == "assistant"
    assert body["master_theme"] == "Own your local market with calm, authority-building dental education."


@pytest.mark.unit
def test_patch_theme_plan_persists_manual_revisions_into_same_draft(test_client, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-dma-3")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps(
            {
                "master_theme": "Trust-first launch",
                "derived_themes": [{"title": "Week 1", "description": "Initial theme", "frequency": "weekly"}],
            }
        ),
    )
    generated = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={"campaign_setup": {"schedule": {"start_date": "2026-03-22", "posts_per_week": 2}}},
    )
    assert generated.status_code == 200, generated.text
    campaign_id = generated.json()["campaign_id"]

    updated = test_client.patch(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "master_theme": "Trust-first launch revised",
            "derived_themes": [
                {"title": "Week 2", "description": "Manual edit", "frequency": "weekly"},
                {"title": "Week 3", "description": "Second edit", "frequency": "weekly"},
            ],
            "campaign_setup": {"schedule": {"start_date": "2026-03-22", "posts_per_week": 2}},
        },
    )

    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["campaign_id"] == campaign_id
    assert body["master_theme"] == "Trust-first launch revised"
    assert len(body["derived_themes"]) == 2
    assert len(campaigns_module._theme_items[campaign_id]) == 2


@pytest.mark.unit
def test_get_workspace_returns_persisted_theme_plan_after_generation(test_client, monkeypatch):
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    customer_id = "cust-dma-4"
    hired_instance_id = _create_marketing_hire(test_client, customer_id=customer_id)

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps(
            {
                "master_theme": "Trust-first launch persisted",
                "derived_themes": [{"title": "Week 1", "description": "Initial theme", "frequency": "weekly"}],
            }
        ),
    )

    generated = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={"customer_id": customer_id, "campaign_setup": {"schedule": {"start_date": "2026-03-22", "posts_per_week": 2}}},
    )
    assert generated.status_code == 200, generated.text

    refreshed = test_client.get(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        params={"customer_id": customer_id},
    )

    assert refreshed.status_code == 200, refreshed.text
    campaign_setup = refreshed.json()["workspace"]["campaign_setup"]
    assert campaign_setup["master_theme"] == "Trust-first launch persisted"
    assert len(campaign_setup["derived_themes"]) == 1
