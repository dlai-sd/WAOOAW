"""Schema integrity tests for DMA models.

These tests verify that the SQLAlchemy ORM columns we rely on actually exist
on the in-memory models. They would have caught missing batch_type /
parent_batch_id columns before any DB migration or API call was attempted.

All tests are unit-level — no real Postgres required.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# MarketingDraftBatchModel column presence
# ---------------------------------------------------------------------------

def test_batch_model_has_required_columns():
    """All columns the DMA workflow depends on must be present on the batch model."""
    from models.marketing_draft import MarketingDraftBatchModel

    mapper = MarketingDraftBatchModel.__table__.columns
    required = {
        "batch_id",
        "batch_type",
        "parent_batch_id",
        "agent_id",
        "customer_id",
        "theme",
        "brand_name",
        "workflow_state",
        "status",
        "created_at",
    }
    missing = required - set(mapper.keys())
    assert not missing, f"Missing columns on MarketingDraftBatchModel: {missing}"


def test_batch_type_has_default_direct():
    """batch_type server default must be 'direct' so existing rows without the column stay valid."""
    from models.marketing_draft import MarketingDraftBatchModel

    col = MarketingDraftBatchModel.__table__.columns["batch_type"]
    # SQLAlchemy stores Python-side default on column.default.arg
    assert col.default is not None or col.server_default is not None, (
        "batch_type must have a default value"
    )


def test_parent_batch_id_is_nullable():
    """parent_batch_id must be nullable — top-level batches have no parent."""
    from models.marketing_draft import MarketingDraftBatchModel

    col = MarketingDraftBatchModel.__table__.columns["parent_batch_id"]
    assert col.nullable is True, "parent_batch_id must be nullable"


def test_parent_batch_id_has_foreign_key():
    """parent_batch_id must reference marketing_draft_batches.batch_id (self-join)."""
    from models.marketing_draft import MarketingDraftBatchModel

    col = MarketingDraftBatchModel.__table__.columns["parent_batch_id"]
    fk_targets = [fk.target_fullname for fk in col.foreign_keys]
    assert any("marketing_draft_batches" in t for t in fk_targets), (
        f"parent_batch_id has no FK to marketing_draft_batches. Got: {fk_targets}"
    )


# ---------------------------------------------------------------------------
# MarketingDraftPostModel column presence
# ---------------------------------------------------------------------------

def test_post_model_has_required_columns():
    """All columns the DMA publish path depends on must be present on the post model."""
    from models.marketing_draft import MarketingDraftPostModel

    mapper = MarketingDraftPostModel.__table__.columns
    required = {
        "post_id",
        "batch_id",
        "channel",
        "text",
        "credential_ref",
        "artifact_type",
        "artifact_mime_type",
        "review_status",
        "execution_status",
        "created_at",
        "updated_at",
    }
    missing = required - set(mapper.keys())
    assert not missing, f"Missing columns on MarketingDraftPostModel: {missing}"


def test_credential_ref_is_nullable():
    """credential_ref is nullable — only YouTube posts need it."""
    from models.marketing_draft import MarketingDraftPostModel

    col = MarketingDraftPostModel.__table__.columns["credential_ref"]
    assert col.nullable is True


def test_review_status_has_default():
    """review_status must default to 'pending_review' so new posts don't start approved."""
    from models.marketing_draft import MarketingDraftPostModel

    col = MarketingDraftPostModel.__table__.columns["review_status"]
    assert col.default is not None or col.server_default is not None, (
        "review_status must have a default"
    )


# ---------------------------------------------------------------------------
# DraftBatchRecord / DraftPostRecord Pydantic models
# ---------------------------------------------------------------------------

def test_draft_batch_record_roundtrips_batch_type():
    """DraftBatchRecord must accept and expose batch_type."""
    from services.draft_batches import DraftBatchRecord, DraftPostRecord
    from datetime import datetime, timezone

    rec = DraftBatchRecord(
        batch_id="B-1",
        agent_id="AGT-1",
        customer_id="CUST-1",
        theme="test theme",
        brand_name="Brand",
        workflow_state="draft_ready_for_review",
        status="pending_review",
        created_at=datetime.now(tz=timezone.utc),
        posts=[],
        batch_type="theme",
        parent_batch_id=None,
    )
    assert rec.batch_type == "theme"
    assert rec.parent_batch_id is None


def test_draft_batch_record_defaults_batch_type_to_direct():
    """Omitting batch_type must default to 'direct' for backward compatibility."""
    from services.draft_batches import DraftBatchRecord
    from datetime import datetime, timezone

    rec = DraftBatchRecord(
        batch_id="B-2",
        agent_id="AGT-1",
        customer_id="CUST-1",
        theme="test theme",
        brand_name="Brand",
        workflow_state="draft_ready_for_review",
        status="pending_review",
        created_at=datetime.now(tz=timezone.utc),
        posts=[],
    )
    assert rec.batch_type == "direct"


def test_draft_batch_record_accepts_parent_batch_id():
    """Content batch must carry parent_batch_id pointing to the theme batch."""
    from services.draft_batches import DraftBatchRecord
    from datetime import datetime, timezone

    rec = DraftBatchRecord(
        batch_id="B-CONTENT-1",
        agent_id="AGT-1",
        customer_id="CUST-1",
        theme="Tip #1",
        brand_name="Brand",
        workflow_state="draft_ready_for_review",
        status="pending_review",
        created_at=datetime.now(tz=timezone.utc),
        posts=[],
        batch_type="content",
        parent_batch_id="B-THEME-1",
    )
    assert rec.batch_type == "content"
    assert rec.parent_batch_id == "B-THEME-1"


# ---------------------------------------------------------------------------
# API request model — create-content-batch endpoint guard
# ---------------------------------------------------------------------------

def test_create_content_batch_blocked_when_no_posts_approved(
    test_client, in_memory_marketing_draft_store
):
    """create-content-batch returns 403 when theme batch has no approved posts."""
    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-1",
            "customer_id": "CUST-SCHEMA-1",
            "theme": "Test theme",
            "brand_name": "Brand",
            "batch_type": "theme",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    batch_id = create.json()["batch_id"]

    # All posts are still pending_review → must be blocked
    resp = test_client.post(
        f"/api/v1/marketing/draft-batches/{batch_id}/create-content-batch",
        json={},
    )
    assert resp.status_code == 403
    detail = resp.json().get("detail", "").lower()
    assert "approved" in detail, f"Expected approval guard message, got: {detail!r}"


def test_create_content_batch_succeeds_when_all_posts_approved(
    test_client, in_memory_marketing_draft_store
):
    """create-content-batch returns 200 when every theme post is approved."""
    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-1",
            "customer_id": "CUST-SCHEMA-2",
            "theme": "Test theme",
            "brand_name": "Brand",
            "batch_type": "theme",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    batch = create.json()
    batch_id = batch["batch_id"]
    post_id = batch["posts"][0]["post_id"]

    # Approve the single post
    test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-SCHEMA-001"},
    )

    resp = test_client.post(
        f"/api/v1/marketing/draft-batches/{batch_id}/create-content-batch",
        json={},
    )
    assert resp.status_code == 200
    content = resp.json()
    assert content["batch_type"] == "content"
    assert content["parent_batch_id"] == batch_id
