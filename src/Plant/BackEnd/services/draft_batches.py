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
