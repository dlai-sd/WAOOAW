from datetime import datetime, timedelta

from services.draft_batches import FileDraftBatchStore
from services.marketing_scheduler import run_due_posts_once


def test_scheduled_posting_runs_due_post_once(test_client, tmp_path, monkeypatch):
    store_path = tmp_path / "draft_batches.jsonl"
    monkeypatch.setenv("DRAFT_BATCH_STORE_PATH", str(store_path))

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

    store = FileDraftBatchStore(str(store_path))
    assert store.update_post(
        post_id,
        review_status="approved",
        execution_status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(seconds=1),
    )

    # First run fails (simulated transient failure), post is marked failed.
    monkeypatch.setenv("MARKETING_FAKE_FAIL_CHANNEL", "youtube")
    executed = run_due_posts_once(store)
    assert executed == 1

    _batch, post = store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "failed"
    assert post.attempts == 1
    assert post.last_error

    # Retry succeeds when failure injection is removed.
    monkeypatch.delenv("MARKETING_FAKE_FAIL_CHANNEL", raising=False)
    executed_retry = run_due_posts_once(store)
    assert executed_retry == 1

    _batch, post = store.find_post(post_id)  # type: ignore[assignment]
    assert post.execution_status == "posted"
    assert post.attempts == 2
    assert post.last_error is None

    # Re-run should be idempotent (post is no longer 'scheduled')
    executed_again = run_due_posts_once(store)
    assert executed_again == 0
