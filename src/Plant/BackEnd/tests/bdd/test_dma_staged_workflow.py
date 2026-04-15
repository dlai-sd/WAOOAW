"""BDD step definitions for DMA staged workflow feature.

Captures customer-expected behaviour from the April 2026 production issues:
  - ValueError: Unsupported local secret ref (wrong adapter)
  - Missing batch_type / parent_batch_id causing workflow to dead-end
  - Approval gate not enforced, letting content be created from unapproved themes

Run with:
  pytest tests/bdd/test_dma_staged_workflow.py -v -k "dma"
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios("features/dma_staged_workflow.feature")


# ─────────────────────────────────────────────────────────────────────────────
# Shared context object
# ─────────────────────────────────────────────────────────────────────────────

class DmaContext:
    def __init__(self) -> None:
        self.customer_id: str = ""
        self.agent_id: str = ""
        self.theme_batch: Dict[str, Any] = {}
        self.content_batch: Dict[str, Any] = {}
        self.last_response: Any = None
        self.secret_backend: str = "local"
        self.adapter: Any = None
        self.adapter_error: Exception | None = None
        self.rejected_post_id: str = ""
        self.publish_response: Any = None


@pytest.fixture
def dma_ctx():
    return DmaContext()


# ─────────────────────────────────────────────────────────────────────────────
# Scenarios 1 & 2 — full staged workflow (uses test_client fixture)
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('a customer "{customer_id}" has hired DMA agent "{agent_id}"'))
def given_customer_hired_agent(dma_ctx, customer_id, agent_id):
    dma_ctx.customer_id = customer_id
    dma_ctx.agent_id = agent_id


@when(parsers.parse('the customer submits a theme batch for "{brand_name}" on channel "{channel}"'))
def when_customer_submits_theme_batch(dma_ctx, test_client, in_memory_marketing_draft_store, brand_name, channel):
    resp = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": dma_ctx.agent_id,
            "hired_instance_id": f"HIRED-BDD-{dma_ctx.customer_id}",
            "customer_id": dma_ctx.customer_id,
            "theme": f"Weekly content plan for {brand_name}",
            "brand_name": brand_name,
            "batch_type": "theme",
            "channels": [channel],
        },
    )
    dma_ctx.theme_batch = resp.json()
    dma_ctx.last_response = resp


@then(parsers.parse('the batch is created with status "{status}"'))
def then_batch_created_with_status(dma_ctx, status):
    assert dma_ctx.last_response.status_code == 200, (
        f"Expected 200, got {dma_ctx.last_response.status_code}"
    )
    assert dma_ctx.theme_batch["status"] == status, (
        f"Expected status={status!r}, got {dma_ctx.theme_batch['status']!r}"
    )


@then('all posts are in state "pending_review"')
def then_all_posts_pending(dma_ctx):
    for post in dma_ctx.theme_batch.get("posts", []):
        assert post["review_status"] == "pending_review", (
            f"Post {post['post_id']} not pending: {post['review_status']}"
        )


@when("the customer approves all posts in the theme batch")
def when_approve_all_posts(dma_ctx, test_client):
    for i, post in enumerate(dma_ctx.theme_batch.get("posts", [])):
        resp = test_client.post(
            f"/api/v1/marketing/draft-posts/{post['post_id']}/approve",
            json={"approval_id": f"APR-BDD-{i:03d}"},
        )
        assert resp.status_code == 200, f"Approve failed: {resp.json()}"


@then(parsers.parse('each post has review_status "{review_status}"'))
def then_each_post_has_review_status(dma_ctx, test_client, review_status):
    batch_id = dma_ctx.theme_batch["batch_id"]
    resp = test_client.get(
        "/api/v1/marketing/draft-batches",
        params={"customer_id": dma_ctx.customer_id},
    )
    assert resp.status_code == 200
    batches = resp.json()
    batch = next((b for b in batches if b["batch_id"] == batch_id), None)
    assert batch is not None, f"Batch {batch_id} not found in list response"
    for post in batch.get("posts", []):
        assert post["review_status"] == review_status, (
            f"Post {post['post_id']} has review_status={post['review_status']!r}, expected {review_status!r}"
        )


@when("the customer triggers content batch creation from the approved theme")
def when_customer_triggers_content_batch(dma_ctx, test_client):
    batch_id = dma_ctx.theme_batch["batch_id"]
    resp = test_client.post(
        f"/api/v1/marketing/draft-batches/{batch_id}/create-content-batch",
        json={},
    )
    dma_ctx.content_batch = resp.json() if resp.status_code == 200 else {}
    dma_ctx.last_response = resp


@then("a new content batch is created linked to the theme batch")
def then_content_batch_created(dma_ctx):
    assert dma_ctx.last_response.status_code == 200, (
        f"Expected 200, got {dma_ctx.last_response.status_code}: {dma_ctx.last_response.json()}"
    )
    assert dma_ctx.content_batch.get("parent_batch_id") == dma_ctx.theme_batch["batch_id"], (
        f"parent_batch_id mismatch: {dma_ctx.content_batch.get('parent_batch_id')!r}"
    )


@then(parsers.parse('the content batch has batch_type "{batch_type}"'))
def then_content_batch_type(dma_ctx, batch_type):
    assert dma_ctx.content_batch.get("batch_type") == batch_type, (
        f"Expected batch_type={batch_type!r}, got {dma_ctx.content_batch.get('batch_type')!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2 — approval gate
# ─────────────────────────────────────────────────────────────────────────────

@when("the customer has NOT approved all posts")
def when_customer_has_not_approved(dma_ctx):
    # No action needed — posts start as pending_review which is the unapproved state
    pass


@when("the customer attempts to create a content batch from the unapproved theme")
def when_attempt_content_batch_unapproved(dma_ctx, test_client):
    batch_id = dma_ctx.theme_batch["batch_id"]
    resp = test_client.post(
        f"/api/v1/marketing/draft-batches/{batch_id}/create-content-batch",
        json={},
    )
    dma_ctx.last_response = resp


@then(parsers.parse("the request is rejected with status {status_code:d}"))
def then_rejected_with_status(dma_ctx, status_code):
    assert dma_ctx.last_response.status_code == status_code, (
        f"Expected {status_code}, got {dma_ctx.last_response.status_code}: "
        f"{dma_ctx.last_response.json()}"
    )


@then(parsers.parse('the rejection reason is "{reason}"'))
def then_rejection_reason(dma_ctx, reason):
    body = dma_ctx.last_response.json()
    # Reason can be in 'reason' field or encoded in 'detail'
    actual_reason = body.get("reason", "") or body.get("detail", "")
    assert reason in actual_reason or reason.replace("_", " ") in actual_reason.lower(), (
        f"Expected reason={reason!r} in response, got: {body}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3 — secret adapter wiring
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('the secret backend is configured as "{backend}"'))
def given_secret_backend(dma_ctx, monkeypatch, backend):
    dma_ctx.secret_backend = backend
    monkeypatch.setenv("SECRET_MANAGER_BACKEND", backend)
    if backend == "local":
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)


@given(parsers.parse('GCP_PROJECT_ID is set to "{project_id}"'))
def given_gcp_project_id(monkeypatch, project_id):
    monkeypatch.setenv("GCP_PROJECT_ID", project_id)


@when("a GCP-format credential ref is read")
def when_gcp_ref_read(dma_ctx):
    import asyncio
    from services.secret_manager_adapter import LocalSecretManagerAdapter

    adapter = LocalSecretManagerAdapter()
    gcp_ref = "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"
    try:
        asyncio.run(adapter.read_secret(gcp_ref))
        dma_ctx.adapter_error = None
    except ValueError as exc:
        dma_ctx.adapter_error = exc


@then(parsers.parse('the adapter raises a ValueError containing "{message}"'))
def then_raises_value_error(dma_ctx, message):
    assert dma_ctx.adapter_error is not None, (
        "Expected a ValueError to be raised, but no error occurred"
    )
    assert message in str(dma_ctx.adapter_error), (
        f"Expected {message!r} in error message, got: {dma_ctx.adapter_error!r}"
    )


@then("the factory returns a GcpSecretManagerAdapter")
def then_factory_returns_gcp_adapter(monkeypatch):
    fake_sm = MagicMock()
    fake_sm.SecretManagerServiceClient.return_value = MagicMock()

    with patch.dict("sys.modules", {
        "google.cloud.secretmanager": fake_sm,
        "google.cloud": MagicMock(secretmanager=fake_sm),
        "google": MagicMock(),
    }):
        import services.secret_manager_adapter as mod
        importlib.reload(mod)
        adapter = mod.get_secret_manager_adapter()
        assert isinstance(adapter, mod.GcpSecretManagerAdapter)

    importlib.reload(mod)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4 — rejected post cannot be published
# ─────────────────────────────────────────────────────────────────────────────

@given(parsers.parse('a customer "{customer_id}" has a content post'))
def given_customer_has_content_post(dma_ctx, test_client, in_memory_marketing_draft_store, customer_id):
    dma_ctx.customer_id = customer_id
    dma_ctx.agent_id = "AGT-MKT-DMA-001"
    resp = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": dma_ctx.agent_id,
            "hired_instance_id": "HIRED-BDD-REJECT",
            "customer_id": customer_id,
            "theme": "Test content",
            "brand_name": "Test Brand",
            "channels": ["youtube"],
        },
    )
    assert resp.status_code == 200
    batch = resp.json()
    dma_ctx.rejected_post_id = batch["posts"][0]["post_id"]


@when(parsers.parse('the customer rejects the post with reason "{reason}"'))
def when_customer_rejects_post(dma_ctx, test_client, reason):
    resp = test_client.post(
        f"/api/v1/marketing/draft-posts/{dma_ctx.rejected_post_id}/reject",
        json={"reason": reason},
    )
    assert resp.status_code == 200, f"Reject failed: {resp.json()}"


@when("the customer attempts to publish the rejected post")
def when_customer_publishes_rejected(dma_ctx, test_client):
    resp = test_client.post(
        f"/api/v1/marketing/draft-posts/{dma_ctx.rejected_post_id}/execute",
        json={
            "agent_id": dma_ctx.agent_id,
            "approval_id": "APR-FAKE-999",
            "intent_action": "publish",
        },
    )
    dma_ctx.publish_response = resp


@then(parsers.parse("the publish request is rejected with status {status_code:d}"))
def then_publish_rejected(dma_ctx, status_code):
    assert dma_ctx.publish_response.status_code == status_code, (
        f"Expected {status_code}, got {dma_ctx.publish_response.status_code}: "
        f"{dma_ctx.publish_response.json()}"
    )
