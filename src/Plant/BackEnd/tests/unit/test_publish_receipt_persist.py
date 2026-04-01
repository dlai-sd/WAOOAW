from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from agent_mold.skills.content_models import PublishReceipt
from services.marketing_scheduler import run_due_posts_once


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
async def test_scheduler_persists_successful_publish_receipt(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    import services.marketing_scheduler as scheduler_module

    async def _fake_publish(inp):
        return PublishReceipt(
            post_id=inp.post.post_id,
            destination_type="youtube",
            success=True,
            platform_post_id="yt-success",
            published_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(
        scheduler_module.default_engine,
        "publish",
        AsyncMock(side_effect=_fake_publish),
    )

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-001",
            "customer_id": "CUST-001",
            "theme": "Clinic hours update",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "cred-youtube-1",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]
    await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-001",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    db = _FakeSession()
    executed = await run_due_posts_once(db=db)

    assert executed == 1
    assert len(db.added) == 1
    assert db.added[0].success is True
    assert db.added[0].platform_post_id == "yt-success"


@pytest.mark.asyncio
async def test_scheduler_persists_failed_publish_receipt(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    import services.marketing_scheduler as scheduler_module

    async def _fake_publish(inp):
        return PublishReceipt(
            post_id=inp.post.post_id,
            destination_type="youtube",
            success=False,
            error="publish failed",
        )

    monkeypatch.setattr(
        scheduler_module.default_engine,
        "publish",
        AsyncMock(side_effect=_fake_publish),
    )

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-001",
            "customer_id": "CUST-001",
            "theme": "Clinic hours update",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "cred-youtube-1",
        },
    )
    post_id = create.json()["posts"][0]["post_id"]
    await in_memory_marketing_draft_store.update_post(
        post_id,
        review_status="approved",
        approval_id="APR-001",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    db = _FakeSession()
    executed = await run_due_posts_once(db=db)

    assert executed == 1
    assert len(db.added) == 1
    assert db.added[0].success is False
    assert db.added[0].error == "publish failed"
