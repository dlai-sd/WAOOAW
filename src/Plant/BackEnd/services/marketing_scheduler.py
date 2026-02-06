"""Marketing scheduled posting runner.

Phase 1: deterministic, idempotent runner that can be invoked by a scheduler.
No external network posting is performed yet.
"""

from __future__ import annotations

import os
from datetime import datetime

from services.draft_batches import FileDraftBatchStore


def run_due_posts_once(store: FileDraftBatchStore, *, now: datetime | None = None) -> int:
    now = now or datetime.utcnow()

    max_attempts = int(os.getenv("MARKETING_SCHEDULER_MAX_ATTEMPTS", "3"))
    fail_channel = os.getenv("MARKETING_FAKE_FAIL_CHANNEL")

    batches = store.load_batches()
    executed = 0
    updated = False

    for batch in batches:
        for post in batch.posts:
            if post.review_status != "approved":
                continue
            if post.execution_status not in {"scheduled", "failed"}:
                continue
            if post.scheduled_at is None or post.scheduled_at > now:
                continue
            if post.attempts >= max_attempts:
                continue

            # Idempotency: we only run scheduled posts; transition away from scheduled means it's done.
            post.execution_status = "running"
            post.attempts += 1

            try:
                # Deterministic placeholder for provider execution.
                # For unit tests we can inject a transient failure by channel.
                if fail_channel and post.channel.value == fail_channel:
                    raise RuntimeError(f"Simulated transient failure for channel={fail_channel}")

                post.execution_status = "posted"
                post.last_error = None
            except Exception as exc:
                post.execution_status = "failed"
                post.last_error = str(exc)

            executed += 1
            updated = True

    if updated:
        store.write_batches(batches)

    return executed
