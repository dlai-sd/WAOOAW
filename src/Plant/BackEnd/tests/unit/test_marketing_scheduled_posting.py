from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from agent_mold.skills.content_models import PublishReceipt
from services.marketing_scheduler import run_due_posts_once
from services.usage_events import InMemoryUsageEventStore, UsageEventType


class _FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, value) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        return None

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_scheduled_posting_runs_due_post_once(test_client, in_memory_marketing_draft_store, monkeypatch):
    async def _fake_publish(inp):
        return PublishReceipt(
            post_id=inp.post.post_id,
            destination_type="youtube",
            success=True,
            platform_post_id=f"yt-{len(inp.post.content_text)}",
            raw_response={"post_url": f"https://www.youtube.com/post/yt-{len(inp.post.content_text)}"},
        )

    import services.marketing_scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module.default_engine, "publish", _fake_publish)

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
    db = _FakeSession()
    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-123",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    monkeypatch.setenv("MARKETING_FAKE_FAIL_CHANNEL", "youtube")
    executed = await run_due_posts_once(usage_events=events, db=db)
    assert executed == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.attempts == 1
    assert post.last_error

    monkeypatch.delenv("MARKETING_FAKE_FAIL_CHANNEL", raising=False)
    monkeypatch.delenv("MARKETING_ALLOWED_CHANNELS", raising=False)
    executed_retry = await run_due_posts_once(usage_events=events, db=db)
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
    assert len(db.added) == 2
    assert db.added[0].success is False
    assert db.added[1].success is True

    executed_again = await run_due_posts_once(usage_events=events, db=db)
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

    executed = await run_due_posts_once(db=_FakeSession())
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

    executed_again = await run_due_posts_once(db=_FakeSession())
    assert executed_again == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.last_error == "credential_ref_required_for_youtube_publish"


@pytest.mark.asyncio
async def test_scheduler_youtube_uses_credential_aware_publish_path(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """Scheduler uses PublisherEngine with resolved credential_ref for YouTube posts."""
    publish_mock = AsyncMock(
        return_value=PublishReceipt(
            post_id="placeholder",
            destination_type="youtube",
            success=True,
            platform_post_id="yt-sched-001",
            raw_response={"post_url": "https://www.youtube.com/post/yt-sched-001"},
        )
    )

    import services.marketing_scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module.default_engine, "publish", publish_mock)

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Credential-aware YouTube post",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-SCHED-001",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    executed = await run_due_posts_once(db=_FakeSession())
    assert executed == 1

    _batch, post = await in_memory_marketing_draft_store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "posted"
    assert post.provider_post_id == "yt-sched-001"

    publish_input = publish_mock.await_args.args[0]
    assert publish_input.credential_ref == "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"
    assert publish_input.post.destination.destination_type == "youtube"


@pytest.mark.asyncio
async def test_scheduler_resolves_attached_youtube_secret_ref_before_publish(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    publish_mock = AsyncMock(
        return_value=PublishReceipt(
            post_id="placeholder",
            destination_type="youtube",
            success=True,
            platform_post_id="yt-sched-002",
            raw_response={"post_url": "https://www.youtube.com/post/yt-sched-002"},
        )
    )

    async def _fake_resolve(db, *, hired_instance_id, supplied_ref):
        assert hired_instance_id == "HIRED-001"
        assert supplied_ref == "cred-youtube-1"
        return "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"

    import services.marketing_scheduler as scheduler_module

    monkeypatch.setattr(scheduler_module.default_engine, "publish", publish_mock)
    monkeypatch.setattr(scheduler_module, "resolve_youtube_secret_ref", _fake_resolve)

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-001",
            "customer_id": "CUST-001",
            "theme": "Credential-aware YouTube post",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "cred-youtube-1",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    assert await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-SCHED-001",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    executed = await run_due_posts_once(db=_FakeSession())
    assert executed == 1
    publish_input = publish_mock.await_args.args[0]
    assert publish_input.credential_ref == "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"
