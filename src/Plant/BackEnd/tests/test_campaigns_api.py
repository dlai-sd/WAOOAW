"""Tests for Campaign Orchestration API — PLANT-CONTENT-1 Iteration 2 (E3 + E4).

E3 tests: campaign create + theme list generation + theme item approval
E4 tests: post generation + post approval

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/test_campaigns_api.py -v \\
      --cov=src/Plant/BackEnd/api/v1/campaigns --cov-fail-under=80
"""
from __future__ import annotations

from typing import AsyncGenerator

import httpx
import pytest
from fastapi import FastAPI


# ─── Helpers ──────────────────────────────────────────────────────────────────

AUTH = "Bearer test-token"

BRIEF_PAYLOAD = {
    "theme": "Hire AI Agents — WAOOAW",
    "start_date": "2026-03-06",
    "duration_days": 7,
    "destinations": [
        {"destination_type": "linkedin"},
        {"destination_type": "instagram"},
        {"destination_type": "simulated"},
    ],
    "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
    "brand_name": "WAOOAW",
    "audience": "SMB founders",
    "tone": "inspiring",
    "approval_mode": "per_item",
}

CREATE_PAYLOAD = {
    "hired_instance_id": "hired-001",
    "customer_id": "cust-001",
    "brief": BRIEF_PAYLOAD,
}


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_stores():
    """Clear in-memory stores before each test for full isolation."""
    import api.v1.campaigns as camp_module
    camp_module._campaigns.clear()
    camp_module._theme_items.clear()
    camp_module._posts.clear()
    yield
    camp_module._campaigns.clear()
    camp_module._theme_items.clear()
    camp_module._posts.clear()


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Isolated async test client — only the campaigns router is mounted."""
    from api.v1.campaigns import router

    app = FastAPI()
    app.include_router(router)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ─── E3-S1-T1: POST create campaign → 201, cost_estimate present ──────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_campaign_returns_201_with_cost_estimate(client, monkeypatch):
    """E3-S1-T1: POST /campaigns with valid brief → 201 + cost_estimate.total_cost_usd == 0.0"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    resp = await client.post("/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH})

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "campaign" in data
    assert "cost_estimate" in data
    assert data["cost_estimate"]["total_cost_usd"] == 0.0
    assert data["campaign"]["status"] == "draft"
    assert len(data["theme_items"]) == 7  # 7 days


# ─── E3-S1-T2: GET theme items → all pending_review ──────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_theme_items_all_pending_review(client, monkeypatch):
    """E3-S1-T2: GET /campaigns/{id}/theme-items → all items in pending_review"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    campaign_id = create_resp.json()["campaign"]["campaign_id"]

    items_resp = await client.get(
        f"/campaigns/{campaign_id}/theme-items", headers={"Authorization": AUTH}
    )
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert len(items) == 7
    for item in items:
        assert item["review_status"] == "pending_review"


# ─── E3-S1-T3: Batch approve all → campaign status theme_approved ─────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_approve_all_theme_items_transitions_campaign_to_theme_approved(
    client, monkeypatch
):
    """E3-S1-T3: Batch approve (empty item_ids) → campaign status = theme_approved"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    campaign_id = create_resp.json()["campaign"]["campaign_id"]

    approve_resp = await client.post(
        f"/campaigns/{campaign_id}/theme-items/approve",
        json={"item_ids": [], "decision": "approved"},
        headers={"Authorization": AUTH},
    )
    assert approve_resp.status_code == 200
    approved_items = approve_resp.json()
    assert len(approved_items) == 7
    for item in approved_items:
        assert item["review_status"] == "approved"

    # Campaign status must now be theme_approved
    campaign_resp = await client.get(
        f"/campaigns/{campaign_id}", headers={"Authorization": AUTH}
    )
    assert campaign_resp.status_code == 200
    assert campaign_resp.json()["status"] == "theme_approved"


# ─── E3-S1-T4: Patch single item → approved ──────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_patch_single_theme_item_sets_approved(client, monkeypatch):
    """E3-S1-T4: PATCH /campaigns/{id}/theme-items/{item_id} with approved → item approved"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    campaign_id = data["campaign"]["campaign_id"]
    item_id = data["theme_items"][0]["theme_item_id"]

    patch_resp = await client.patch(
        f"/campaigns/{campaign_id}/theme-items/{item_id}",
        json={"decision": "approved"},
        headers={"Authorization": AUTH},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["review_status"] == "approved"
    assert patch_resp.json()["theme_item_id"] == item_id


# ─── E3-S1-T5: No auth header → 401 ─────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_no_auth_header_returns_401(client, monkeypatch):
    """E3-S1-T5: All routes return 401 when Authorization header is absent"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    # POST /campaigns without auth
    resp_create = await client.post("/campaigns", json=CREATE_PAYLOAD)
    assert resp_create.status_code == 401

    # GET /campaigns/{id} without auth
    resp_get = await client.get("/campaigns/some-id")
    assert resp_get.status_code == 401

    # GET /campaigns/{id}/theme-items without auth
    resp_items = await client.get("/campaigns/some-id/theme-items")
    assert resp_items.status_code == 401


# ─── E4-S1-T1: generate-posts on approved theme item → posts created ──────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_posts_for_approved_theme_item(client, monkeypatch):
    """E4-S1-T1: generate-posts on approved theme item → posts list, one per destination"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    # Create campaign
    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    campaign_id = data["campaign"]["campaign_id"]
    item_id = data["theme_items"][0]["theme_item_id"]

    # Approve that theme item first
    await client.patch(
        f"/campaigns/{campaign_id}/theme-items/{item_id}",
        json={"decision": "approved"},
        headers={"Authorization": AUTH},
    )

    # Generate posts
    posts_resp = await client.post(
        f"/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts",
        headers={"Authorization": AUTH},
    )
    assert posts_resp.status_code == 201
    posts = posts_resp.json()
    # 3 destinations → 3 posts
    assert len(posts) == 3
    for post in posts:
        assert post["review_status"] == "pending_review"
        assert post["publish_status"] == "not_published"
        assert isinstance(post["content_text"], str)
        assert len(post["content_text"]) > 0


# ─── E4-S1-T2: generate-posts on pending theme item → 409 ────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_generate_posts_for_pending_theme_item_returns_409(client, monkeypatch):
    """E4-S1-T2: generate-posts on pending_review theme item → 409"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    campaign_id = data["campaign"]["campaign_id"]
    item_id = data["theme_items"][0]["theme_item_id"]  # still pending_review

    posts_resp = await client.post(
        f"/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts",
        headers={"Authorization": AUTH},
    )
    assert posts_resp.status_code == 409


# ─── E4-S1-T3: GET posts with ?destination_type filters correctly ─────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_posts_filtered_by_destination_type(client, monkeypatch):
    """E4-S1-T3: GET /campaigns/{id}/posts?destination_type=linkedin filters correctly"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    campaign_id = data["campaign"]["campaign_id"]
    item_id = data["theme_items"][0]["theme_item_id"]

    # Approve theme item
    await client.patch(
        f"/campaigns/{campaign_id}/theme-items/{item_id}",
        json={"decision": "approved"},
        headers={"Authorization": AUTH},
    )

    # Generate posts (3 destinations: linkedin, instagram, simulated)
    await client.post(
        f"/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts",
        headers={"Authorization": AUTH},
    )

    # Filter by destination_type=linkedin → exactly 1 post
    filtered_resp = await client.get(
        f"/campaigns/{campaign_id}/posts",
        params={"destination_type": "linkedin"},
        headers={"Authorization": AUTH},
    )
    assert filtered_resp.status_code == 200
    filtered_posts = filtered_resp.json()
    assert len(filtered_posts) == 1
    assert filtered_posts[0]["destination"]["destination_type"] == "linkedin"

    # No filter → all 3 posts
    all_resp = await client.get(
        f"/campaigns/{campaign_id}/posts", headers={"Authorization": AUTH}
    )
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 3


# ─── E4-S1-T4: Batch approve posts → all approved ────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_approve_posts_sets_all_approved(client, monkeypatch):
    """E4-S1-T4: POST /campaigns/{id}/posts/approve with empty post_ids → all approved"""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")

    create_resp = await client.post(
        "/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    campaign_id = data["campaign"]["campaign_id"]
    item_id = data["theme_items"][0]["theme_item_id"]

    # Approve theme item
    await client.patch(
        f"/campaigns/{campaign_id}/theme-items/{item_id}",
        json={"decision": "approved"},
        headers={"Authorization": AUTH},
    )

    # Generate posts
    await client.post(
        f"/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts",
        headers={"Authorization": AUTH},
    )

    # Batch approve all posts
    approve_resp = await client.post(
        f"/campaigns/{campaign_id}/posts/approve",
        json={"post_ids": [], "decision": "approved"},
        headers={"Authorization": AUTH},
    )
    assert approve_resp.status_code == 200
    approved_posts = approve_resp.json()
    assert len(approved_posts) == 3
    for post in approved_posts:
        assert post["review_status"] == "approved"

    # Verify via list endpoint
    all_resp = await client.get(
        f"/campaigns/{campaign_id}/posts", headers={"Authorization": AUTH}
    )
    for post in all_resp.json():
        assert post["review_status"] == "approved"
