"""Tests for Content Creator API — unified create → approve → publish flow."""

import pytest

from integrations.social.base import SocialPostResult


def test_create_content_returns_draft_batch(test_client, in_memory_marketing_draft_store):
    """POST /content-creator/create generates drafts for customer review."""
    payload = {
        "agent_id": "AGT-MKT-HEALTH-001",
        "theme": "5 tips for healthy living",
        "brand_name": "HealthFirst",
        "customer_id": "CUST-001",
        "brief_summary": "Health tips for YouTube audience",
    }
    resp = test_client.post("/api/v1/content-creator/create", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["batch_id"]
    assert data["agent_id"] == "AGT-MKT-HEALTH-001"
    assert data["customer_id"] == "CUST-001"
    assert data["status"] == "pending_review"
    assert data["workflow_state"] == "draft_ready_for_review"
    assert len(data["posts"]) == 5  # default 5 channels
    assert all(p["review_status"] == "pending_review" for p in data["posts"])


def test_list_batches_filters_by_customer(test_client, in_memory_marketing_draft_store):
    """GET /content-creator/batches filters by customer_id."""
    test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Topic A",
            "brand_name": "Brand A",
            "customer_id": "CUST-A",
        },
    )
    test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Topic B",
            "brand_name": "Brand B",
            "customer_id": "CUST-B",
        },
    )

    resp = test_client.get("/api/v1/content-creator/batches", params={"customer_id": "CUST-A"})
    assert resp.status_code == 200
    batches = resp.json()
    assert len(batches) == 1
    assert batches[0]["customer_id"] == "CUST-A"


def test_get_batch_by_id(test_client, in_memory_marketing_draft_store):
    """GET /content-creator/batches/{id} returns a single batch."""
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Single batch test",
            "brand_name": "TestBrand",
            "customer_id": "CUST-001",
        },
    )
    batch_id = create.json()["batch_id"]

    resp = test_client.get(f"/api/v1/content-creator/batches/{batch_id}")
    assert resp.status_code == 200
    assert resp.json()["batch_id"] == batch_id


def test_get_batch_not_found(test_client, in_memory_marketing_draft_store):
    """GET /content-creator/batches/{id} returns 403 for unknown batch."""
    resp = test_client.get("/api/v1/content-creator/batches/BATCH-NONEXISTENT")
    assert resp.status_code == 403


def test_approve_post_sets_approved_status(test_client, in_memory_marketing_draft_store):
    """POST /content-creator/posts/{id}/approve transitions to approved."""
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Approve test",
            "brand_name": "TestBrand",
            "customer_id": "CUST-001",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]

    resp = test_client.post(
        f"/api/v1/content-creator/posts/{post_id}/approve",
        json={"approval_id": "APR-TEST-001"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["post_id"] == post_id
    assert body["review_status"] == "approved"
    assert body["approval_id"] == "APR-TEST-001"


def test_approve_generates_approval_id_if_missing(test_client, in_memory_marketing_draft_store):
    """Approval auto-generates an approval_id when not provided."""
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Auto approve ID",
            "brand_name": "TestBrand",
            "customer_id": "CUST-001",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]

    resp = test_client.post(
        f"/api/v1/content-creator/posts/{post_id}/approve",
        json={},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["approval_id"].startswith("APR-")


def test_reject_post_sets_rejected_status(test_client, in_memory_marketing_draft_store):
    """POST /content-creator/posts/{id}/reject transitions to rejected."""
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Reject test",
            "brand_name": "TestBrand",
            "customer_id": "CUST-001",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]

    resp = test_client.post(f"/api/v1/content-creator/posts/{post_id}/reject")
    assert resp.status_code == 200
    body = resp.json()
    assert body["post_id"] == post_id
    assert body["review_status"] == "rejected"


def test_publish_unapproved_post_fails(test_client, in_memory_marketing_draft_store):
    """POST /content-creator/posts/{id}/publish rejects unapproved posts."""
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-001",
            "theme": "Unapproved publish",
            "brand_name": "TestBrand",
            "customer_id": "CUST-001",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]

    resp = test_client.post(f"/api/v1/content-creator/posts/{post_id}/publish")
    assert resp.status_code == 403
    assert resp.json()["reason"] == "not_approved"


def test_publish_nonexistent_post_fails(test_client, in_memory_marketing_draft_store):
    """POST /content-creator/posts/{id}/publish returns 403 for unknown post."""
    resp = test_client.post("/api/v1/content-creator/posts/POST-NONEXISTENT/publish")
    assert resp.status_code == 403
    assert resp.json()["reason"] == "unknown_post_id"


def test_full_create_approve_publish_youtube_flow(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """Full end-to-end: create → approve → publish to YouTube."""

    # 1. Create content with YouTube channel
    create = test_client.post(
        "/api/v1/content-creator/create",
        json={
            "agent_id": "AGT-MKT-001",
            "customer_id": "CUST-001",
            "theme": "YouTube publish test",
            "brand_name": "TestBrand",
            "youtube_credential_ref": "CRED-yt-test",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    posts = create.json()["posts"]
    yt_post = next(p for p in posts if p["channel"] == "youtube")
    post_id = yt_post["post_id"]

    # 2. Approve
    approve = test_client.post(
        f"/api/v1/content-creator/posts/{post_id}/approve",
        json={"approval_id": "APR-YT-FULL"},
    )
    assert approve.status_code == 200
    assert approve.json()["review_status"] == "approved"

    # 3. Publish — mock YouTubeClient
    async def _fake_post_text(self, *, credential_ref, text, image_url=None):
        return SocialPostResult(
            success=True,
            platform="youtube",
            post_id="yt-vid-xyz",
            post_url="https://www.youtube.com/post/yt-vid-xyz",
        )

    import integrations.social.youtube_client as yt_module
    monkeypatch.setattr(yt_module.YouTubeClient, "post_text", _fake_post_text)

    publish = test_client.post(f"/api/v1/content-creator/posts/{post_id}/publish")
    assert publish.status_code == 200
    body = publish.json()
    assert body["execution_status"] == "posted"
    assert body["provider_post_id"] == "yt-vid-xyz"
    assert body["provider_post_url"] == "https://www.youtube.com/post/yt-vid-xyz"
    assert body["channel"] == "youtube"

    # 4. Verify persisted state
    updated_post = None
    for batch in in_memory_marketing_draft_store._batches.values():
        for p in batch.posts:
            if p.post_id == post_id:
                updated_post = p
                break
    assert updated_post is not None
    assert updated_post.execution_status == "posted"
    assert updated_post.provider_post_id == "yt-vid-xyz"
