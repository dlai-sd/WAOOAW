from datetime import datetime, timedelta

import pytest

from services.marketing_scheduler import run_due_posts_once
from services.usage_events import InMemoryUsageEventStore, UsageEventType


@pytest.mark.asyncio
async def test_scheduled_posting_runs_due_post_once(test_client, in_memory_marketing_draft_store, monkeypatch):
    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Clinic hours update",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest",
        },
    )
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    events = InMemoryUsageEventStore()
    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-123",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    monkeypatch.setenv("MARKETING_FAKE_FAIL_CHANNEL", "youtube")
    executed = await run_due_posts_once(usage_events=events, db=object())
    assert executed == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.attempts == 1
    assert post.last_error

    monkeypatch.delenv("MARKETING_FAKE_FAIL_CHANNEL", raising=False)
    monkeypatch.delenv("MARKETING_ALLOWED_CHANNELS", raising=False)
    executed_retry = await run_due_posts_once(usage_events=events, db=object())
    assert executed_retry == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "posted"
    assert post.attempts == 2
    assert post.last_error is None
    assert post.provider_post_id
    assert post.provider_post_url

    publish_events = events.list_events(event_type=UsageEventType.PUBLISH_ACTION, limit=None)
    assert len(publish_events) == 1
    assert publish_events[0].correlation_id == f"draft_post:{post_id}"

    executed_again = await run_due_posts_once(usage_events=events, db=object())
    assert executed_again == 0


@pytest.mark.asyncio
async def test_scheduler_rejects_youtube_without_approval_or_credential_ref(test_client, in_memory_marketing_draft_store):
    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Clinic hours update",
            "brand_name": "Care Clinic",
        },
    )
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    executed = await run_due_posts_once(db=object())
    assert executed == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.last_error == "approval_required_for_youtube_publish"

    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        approval_id="APR-123",
        execution_status="scheduled",
        last_error=None,
    )

    executed_again = await run_due_posts_once(db=object())
    assert executed_again == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.last_error == "credential_ref_required_for_youtube_publish"
