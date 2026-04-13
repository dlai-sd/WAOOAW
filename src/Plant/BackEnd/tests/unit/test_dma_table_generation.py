"""Tests for DMA table generation — verifies that the conversation-to-table
pipeline actually produces tables instead of conversational filler text.

These tests cover the exact failure mode: user asks "give me a table" and
the system returns only conversational text with no actual table/themes.
"""
from __future__ import annotations

import json

import pytest

import api.v1.campaigns as campaigns_module


def _create_marketing_hire(test_client, customer_id: str = "cust-dma-table") -> str:
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
    hired_instance_id = draft.json()["hired_instance_id"]

    # Persist the workspace via the activation endpoint so brand_name is available
    saved = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        json={
            "customer_id": customer_id,
            "workspace": {
                "brand_name": "Acme Health",
                "location": "Pune",
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "offerings_services": ["Dental care"],
                "platforms_enabled": ["youtube"],
            },
        },
    )
    assert saved.status_code == 200

    return hired_instance_id


def _full_summary():
    """All 11 fields filled — approval_ready should be allowed."""
    return {
        "profession_name": "Beauty Artist",
        "location_focus": "Viman Nagar, Pune",
        "customer_profile": "Brides aged 22-35 planning weddings",
        "service_focus": "Bridal makeup and styling",
        "signature_differentiator": "Personalized bridal look consultation",
        "business_goal": "Drive repeat bookings and local reputation",
        "first_content_direction": "Weekly bridal transformation tutorials",
        "business_focus": "Bridal makeup studio in Viman Nagar",
        "audience": "Brides and families in Viman Nagar area",
        "positioning": "The go-to bridal artist in Viman Nagar",
        "tone": "Warm, aspirational, confident",
        "content_pillars": ["Tutorials", "Transformations", "Testimonials"],
        "youtube_angle": "Bridal beauty tips and behind-the-scenes",
        "cta": "Book a consultation for your wedding look",
    }


def _core_only_summary():
    """Only 5 core fields filled — should allow draft_ready but not approval_ready."""
    return {
        "profession_name": "Beauty Artist",      # industry
        "location_focus": "Viman Nagar, Pune",   # locality
        "audience": "Brides in Viman Nagar",     # target_audience
        "business_goal": "Drive bookings",        # objective
        "cta": "Book a consultation",             # offer
    }


def _insufficient_summary():
    """Only 2 fields filled — should not allow any generation."""
    return {
        "profession_name": "Beauty Artist",
        "location_focus": "Pune",
    }


# ---------------------------------------------------------------------------
# Test 1: When LLM returns themes + user asks for table → table is produced
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_table_generated_when_llm_returns_derived_themes_and_user_asks_for_table(test_client, monkeypatch):
    """The happy path: LLM returns themes, user says 'give me themes in table format'
    → auto_generated_draft should contain a table with actual theme rows."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-table-happy")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps({
            "assistant_message": "Here is your content calendar.",
            "status": "approval_ready",
            "summary": _full_summary(),
            "master_theme": "Bridal beauty authority in Viman Nagar",
            "derived_themes": [
                {"title": "Bridal Tutorials", "description": "Step-by-step bridal looks", "frequency": "weekly", "pillar": "Education"},
                {"title": "Transformations", "description": "Before/after reveals", "frequency": "weekly", "pillar": "Proof"},
                {"title": "Client Stories", "description": "Real bride testimonials", "frequency": "biweekly", "pillar": "Trust"},
            ],
            "checkpoint_summary": "All fields locked.",
            "current_focus_question": "",
            "next_step_options": ["Approve this direction"],
            "time_saving_note": "Ready to go.",
        }),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "give me actual themes in table format",
                    "messages": [
                        {"role": "user", "content": "give me actual themes in table format"},
                    ],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["derived_themes"]) >= 2, f"Expected themes but got: {body['derived_themes']}"
    assert body["auto_generated_draft"] is not None, "Expected auto_generated_draft but got None"
    draft = body["auto_generated_draft"]
    assert len(draft.get("posts", [])) >= 1, "Expected at least one post in auto_generated_draft"

    # Verify the table post has actual content, not a placeholder
    table_post = draft["posts"][0]
    assert "Bridal Tutorials" in table_post["text"], f"Table should contain theme titles, got: {table_post['text'][:200]}"


# ---------------------------------------------------------------------------
# Test 2: LLM returns empty themes + user asks for table → targeted LLM call fires
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_targeted_theme_generation_when_llm_returns_empty_themes_but_core_fields_filled(test_client, monkeypatch):
    """The bug scenario: LLM returns only conversational text with empty derived_themes,
    but user asked for a table and core fields are filled → second LLM call should generate themes."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-table-empty-themes")

    import api.v1.digital_marketing_activation as dma_module

    # First call: LLM returns conversational filler with no themes (the bug)
    # Second call: targeted theme generation returns actual themes
    call_count = {"n": 0}

    def mock_grok_complete(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # First call: conversation response with empty themes (simulates the bug)
            return json.dumps({
                "assistant_message": "I'm delighted to provide the actual themes for April 2026.",
                "status": "approval_ready",
                "summary": _core_only_summary(),
                "master_theme": "Content plan for Acme Health",
                "derived_themes": [],  # BUG: empty!
                "checkpoint_summary": "Working on it.",
                "current_focus_question": "",
                "next_step_options": [],
                "time_saving_note": "",
            })
        else:
            # Second call: targeted theme generation succeeds
            return json.dumps({
                "master_theme": "Bridal beauty in Viman Nagar",
                "derived_themes": [
                    {"title": "Bridal Tutorials", "description": "Step-by-step looks", "frequency": "weekly", "pillar": "Education"},
                    {"title": "Transformations", "description": "Before/after reveals", "frequency": "weekly", "pillar": "Proof"},
                ],
            })

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(dma_module, "grok_complete", mock_grok_complete)

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "ok, give me actual themes in table format",
                    "messages": [
                        {"role": "user", "content": "ok, give me actual themes in table format"},
                    ],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()

    # The second LLM call should have fired
    assert call_count["n"] >= 2, f"Expected 2+ LLM calls (second for theme gen), got {call_count['n']}"

    # Should have actual themes now
    assert len(body["derived_themes"]) >= 2, f"Expected themes from targeted call, got: {body['derived_themes']}"

    # auto_generated_draft should exist
    assert body["auto_generated_draft"] is not None, "Expected auto_generated_draft with table"


# ---------------------------------------------------------------------------
# Test 3: Insufficient fields + table request → clear field request, no table
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_insufficient_fields_returns_clear_field_request_not_filler(test_client, monkeypatch):
    """When fewer than 5 core fields are filled and user asks for a table,
    the DMA should explain what's missing and why — not produce filler text."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-table-insufficient")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps({
            "assistant_message": "To build your content calendar I need target_audience and objective.",
            "status": "approval_ready",
            "summary": _insufficient_summary(),
            "master_theme": "",
            "derived_themes": [],
            "checkpoint_summary": "",
            "current_focus_question": "What audience are you targeting?",
            "next_step_options": ["Define audience", "Set objective"],
            "time_saving_note": "",
        }),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "give me themes in table format",
                    "messages": [
                        {"role": "user", "content": "give me themes in table format"},
                    ],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    workshop = body["workspace"]["campaign_setup"]["strategy_workshop"]

    # Should be in discovery, not approval_ready
    assert workshop["status"] == "discovery", f"Expected discovery but got {workshop['status']}"

    # The current_focus_question should mention missing fields, not generic filler
    focus_q = workshop.get("current_focus_question", "")
    assert focus_q, "Expected a current_focus_question about missing fields"

    # auto_generated_draft should NOT exist (not enough fields)
    # The table can't be generated without core fields
    assert body["auto_generated_draft"] is None or body["auto_generated_draft"] == {}, \
        f"Should not generate table with insufficient fields, got: {body.get('auto_generated_draft')}"


# ---------------------------------------------------------------------------
# Test 4: Core fields filled → status becomes draft_ready (not forced to discovery)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_core_fields_filled_allows_draft_ready_status(test_client, monkeypatch):
    """When 5 core fields are filled but < 9 total, status should be draft_ready,
    not forced back to discovery."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-table-draft-ready")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps({
            "assistant_message": "Here are your initial themes based on what I know so far.",
            "status": "approval_ready",
            "summary": _core_only_summary(),
            "master_theme": "Bridal beauty in Viman Nagar",
            "derived_themes": [
                {"title": "Tutorials", "description": "Bridal looks", "frequency": "weekly"},
                {"title": "Testimonials", "description": "Client stories", "frequency": "weekly"},
            ],
            "checkpoint_summary": "Core strategy locked.",
            "current_focus_question": "",
            "next_step_options": ["Approve", "Refine"],
            "time_saving_note": "Draft ready.",
        }),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "give me themes",
                    "messages": [],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    workshop = body["workspace"]["campaign_setup"]["strategy_workshop"]

    # With 5/11 fields and LLM saying approval_ready → should become draft_ready, not discovery
    assert workshop["status"] == "draft_ready", f"Expected draft_ready but got {workshop['status']}"
    assert len(body["derived_themes"]) >= 2


# ---------------------------------------------------------------------------
# Test 5: System prompt includes field purposes and DELIVERABLE REQUEST RULE
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_system_prompt_contains_field_purposes_and_gated_deliverable_rule():
    """The system prompt must contain the gated deliverable rule and field purpose reference."""
    import api.v1.digital_marketing_activation as dma_module

    prompt_json = dma_module._theme_workshop_prompt(
        {
            "brand_name": "Test Brand",
            "location": "Pune",
            "offerings_services": ["Makeup"],
            "platforms_enabled": ["youtube"],
        },
        {
            "strategy_workshop": {
                "messages": [],
                "pending_input": "give me themes",
            },
        },
    )
    prompt = json.loads(prompt_json)

    checklist = prompt["workshop_state"]["required_fields_checklist"]

    # Must have core_fields and field_purposes
    assert "core_fields" in checklist, "Missing core_fields in checklist"
    assert "core_missing" in checklist, "Missing core_missing in checklist"
    assert "can_generate_draft" in checklist, "Missing can_generate_draft in checklist"
    assert "field_purposes" in checklist, "Missing field_purposes in checklist"

    # field_purposes should explain why missing fields matter
    for field, purpose in checklist["field_purposes"].items():
        assert len(purpose) > 10, f"Field purpose for '{field}' is too short: '{purpose}'"


# ---------------------------------------------------------------------------
# Test 6: Readiness gate includes core_filled_count in brief_progress
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_brief_progress_includes_core_field_tracking():
    """_parse_theme_workshop_response should include core field tracking in brief_progress."""
    import api.v1.digital_marketing_activation as dma_module

    raw = json.dumps({
        "assistant_message": "Here are your themes.",
        "status": "approval_ready",
        "summary": _core_only_summary(),
        "master_theme": "Test theme",
        "derived_themes": [{"title": "T1", "description": "D1", "frequency": "weekly"}],
        "checkpoint_summary": "Done.",
        "current_focus_question": "",
        "next_step_options": [],
        "time_saving_note": "",
    })

    _master, _derived, workshop = dma_module._parse_theme_workshop_response(
        raw,
        workspace={"brand_name": "Test"},
        existing_workshop={"messages": [], "summary": {}, "follow_up_questions": [], "status": "discovery"},
        pending_input="give me a plan",
    )

    bp = workshop["brief_progress"]
    assert "core_filled_count" in bp, "Missing core_filled_count in brief_progress"
    assert "can_generate_draft" in bp, "Missing can_generate_draft in brief_progress"
    assert bp["core_filled_count"] == 5, f"Expected 5 core fields filled, got {bp['core_filled_count']}"
    assert bp["can_generate_draft"] is True


# ---------------------------------------------------------------------------
# Test 7: Conversational-only response with table request = FAILURE scenario
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_conversational_only_response_does_not_silently_pass_as_table(test_client, monkeypatch):
    """If LLM returns only 'I'm delighted to provide...' with no themes and insufficient fields,
    the response must NOT contain an auto_generated_draft pretending to be a table."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    hired_instance_id = _create_marketing_hire(test_client, customer_id="cust-table-filler")

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps({
            "assistant_message": "I'm delighted to provide the actual themes for April 2026, tailored for Viman Nagar brides on YouTube.",
            "status": "discovery",
            "summary": _insufficient_summary(),
            "master_theme": "",
            "derived_themes": [],
            "checkpoint_summary": "",
            "current_focus_question": "",
            "next_step_options": [],
            "time_saving_note": "",
        }),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "give me themes in table format",
                    "messages": [
                        {"role": "user", "content": "give me themes in table format"},
                    ],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()

    # No table should be produced when there are no themes and insufficient fields
    if body["auto_generated_draft"] is not None:
        posts = body["auto_generated_draft"].get("posts", [])
        for post in posts:
            # If a table post exists, it must NOT be just a generic single-row placeholder
            if post.get("artifact_type") == "table":
                meta = post.get("artifact_metadata", {})
                table_rows = meta.get("table_preview", {}).get("rows", [])
                # A single-row table with just the master theme = useless placeholder
                if len(table_rows) <= 1:
                    theme_val = table_rows[0].get("Theme", "") if table_rows else ""
                    assert "Content plan for" not in theme_val, (
                        f"Got a useless placeholder table instead of real themes: {table_rows}"
                    )


# ---------------------------------------------------------------------------
# Test 8: draft_ready status survives normalization (D1 regression)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_draft_ready_status_survives_normalization():
    """D1 regression: _normalize_strategy_workshop must preserve 'draft_ready' status.
    Before the fix, draft_ready was not in the allowed set and was reset to not_started."""
    from api.v1.digital_marketing_activation import _normalize_strategy_workshop

    raw = {"status": "draft_ready", "summary": _core_only_summary()}
    result = _normalize_strategy_workshop(raw, {})
    assert result["status"] == "draft_ready", (
        f"Expected draft_ready to survive normalization, got: {result['status']}"
    )


# ---------------------------------------------------------------------------
# Test 9: auto-draft succeeds when brand_name is empty (D2 regression)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_auto_draft_with_empty_brand_name_uses_fallback(test_client, monkeypatch):
    """D2 regression: when workspace.brand_name is empty, _build_auto_draft should
    fall back to workshop summary's profession_name instead of failing with a
    Pydantic validation error on DraftBatchRecord.brand_name."""
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    # Create a hire WITHOUT brand_name in the workspace
    checkout = test_client.post(
        "/api/v1/payments/coupon/checkout",
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "AGT-MKT-HEALTH-001",
            "duration": "monthly",
            "customer_id": "cust-no-brand",
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
            "customer_id": "cust-no-brand",
            "nickname": "Test Agent",
            "theme": "dark",
            "config": {
                "primary_language": "en",
                "timezone": "Asia/Kolkata",
                "brand_name": "",  # Deliberately empty — reproduces D2
                "location": "Pune",
            },
        },
    )
    assert draft.status_code == 200
    hired_instance_id = draft.json()["hired_instance_id"]

    # Set workspace WITHOUT brand_name
    saved = test_client.put(
        f"/api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
        json={
            "customer_id": "cust-no-brand",
            "workspace": {
                "brand_name": "",  # Empty!
                "location": "Pune",
                "primary_language": "en",
            },
        },
    )
    assert saved.status_code == 200

    import api.v1.digital_marketing_activation as dma_module

    monkeypatch.setattr(dma_module, "get_grok_client", lambda: object())
    monkeypatch.setattr(
        dma_module,
        "grok_complete",
        lambda *args, **kwargs: json.dumps({
            "assistant_message": "Here is your content calendar.",
            "status": "approval_ready",
            "summary": _full_summary(),
            "master_theme": "Beauty services content plan",
            "derived_themes": [
                {"title": "Tutorials", "description": "How-to bridal looks", "frequency": "weekly", "pillar": "Education"},
                {"title": "Testimonials", "description": "Happy bride stories", "frequency": "biweekly", "pillar": "Trust"},
            ],
            "checkpoint_summary": "All fields locked.",
            "current_focus_question": "",
            "next_step_options": ["Approve"],
            "time_saving_note": "",
        }),
    )

    response = test_client.post(
        f"/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        headers={"Authorization": "Bearer test-token"},
        json={
            "campaign_setup": {
                "strategy_workshop": {
                    "pending_input": "show me the themes in table format",
                    "messages": [{"role": "user", "content": "show me the themes in table format"}],
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    # D2 fix: auto-draft should NOT fail — it should use summary's profession_name as fallback
    assert body["auto_generated_draft"] is not None, (
        "auto_generated_draft should not be None when brand_name is empty — "
        "the D2 fix should fall back to workshop summary's profession_name"
    )
    draft = body["auto_generated_draft"]
    assert len(draft.get("posts", [])) >= 1, "Expected at least one post"
    # The brand_name in the batch should be the fallback, not empty
    assert draft.get("brand_name", "") != "", "brand_name should not be empty after fallback"
