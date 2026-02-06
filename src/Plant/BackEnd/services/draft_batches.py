"""Draft batch storage.

Phase 1 (Plant + PP): store draft batches for ops-assisted review.
This uses a file-backed store to keep unit tests DB-free.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from agent_mold.skills.playbook import ChannelName


_UNSET = object()


DraftReviewStatus = Literal["pending_review", "approved", "changes_requested", "rejected"]
DraftExecutionStatus = Literal["not_scheduled", "scheduled", "running", "posted", "failed"]


class DraftPostRecord(BaseModel):
    post_id: str = Field(..., min_length=1)
    channel: ChannelName
    text: str = Field(..., min_length=1)
    hashtags: List[str] = Field(default_factory=list)

    review_status: DraftReviewStatus = "pending_review"
    execution_status: DraftExecutionStatus = "not_scheduled"

    scheduled_at: Optional[datetime] = None

    attempts: int = 0
    last_error: Optional[str] = None


class DraftBatchRecord(BaseModel):
    batch_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    customer_id: Optional[str] = None

    theme: str = Field(..., min_length=1)
    brand_name: str = Field(..., min_length=1)

    created_at: datetime
    status: DraftReviewStatus = "pending_review"

    posts: List[DraftPostRecord] = Field(default_factory=list)


class FileDraftBatchStore:
    def __init__(self, path: str):
        self._path = Path(path)

    def save_batch(self, batch: DraftBatchRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(batch.model_dump_json())
            f.write("\n")

    def find_post(self, post_id: str) -> tuple[DraftBatchRecord, DraftPostRecord] | None:
        for batch in self.load_batches():
            for post in batch.posts:
                if post.post_id == post_id:
                    return batch, post
        return None

    def load_batches(self) -> List[DraftBatchRecord]:
        if not self._path.exists():
            return []

        batches: List[DraftBatchRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            batches.append(DraftBatchRecord.model_validate_json(line))
        return batches

    def write_batches(self, batches: List[DraftBatchRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for batch in batches:
                f.write(batch.model_dump_json())
                f.write("\n")

    def update_post(
        self,
        post_id: str,
        *,
        review_status: DraftReviewStatus | object = _UNSET,
        execution_status: DraftExecutionStatus | object = _UNSET,
        scheduled_at: datetime | None | object = _UNSET,
        attempts: int | object = _UNSET,
        last_error: str | None | object = _UNSET,
    ) -> bool:
        batches = self.load_batches()
        updated = False

        for batch in batches:
            for post in batch.posts:
                if post.post_id != post_id:
                    continue
                if review_status is not _UNSET:
                    post.review_status = review_status
                if execution_status is not _UNSET:
                    post.execution_status = execution_status
                if scheduled_at is not _UNSET:
                    post.scheduled_at = scheduled_at
                if attempts is not _UNSET:
                    post.attempts = attempts
                if last_error is not _UNSET:
                    post.last_error = last_error
                updated = True
                break

        if updated:
            self.write_batches(batches)

        return updated
