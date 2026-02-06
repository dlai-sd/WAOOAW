"""Marketing draft batch endpoints.

Phase 1: Plant supports generating a persisted draft batch for review.
No external posting occurs in this module.
"""

from __future__ import annotations

import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ChannelName, SkillExecutionInput
from services.draft_batches import DraftBatchRecord, DraftPostRecord, FileDraftBatchStore


router = APIRouter(prefix="/marketing", tags=["marketing"])


@lru_cache(maxsize=1)
def _marketing_multichannel_playbook():
    path = (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )
    return load_playbook(path)


def get_draft_batch_store() -> FileDraftBatchStore:
    path = os.getenv("DRAFT_BATCH_STORE_PATH", "/app/data/draft_batches.jsonl")
    return FileDraftBatchStore(path)


class CreateDraftBatchRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    customer_id: Optional[str] = None

    theme: str
    brand_name: str
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None

    channels: Optional[List[ChannelName]] = None


class CreateDraftBatchResponse(DraftBatchRecord):
    pass


@router.post("/draft-batches", response_model=CreateDraftBatchResponse)
async def create_draft_batch(
    body: CreateDraftBatchRequest,
    store: FileDraftBatchStore = Depends(get_draft_batch_store),
) -> CreateDraftBatchResponse:
    playbook = _marketing_multichannel_playbook()

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme=body.theme,
            brand_name=body.brand_name,
            offer=body.offer,
            location=body.location,
            audience=body.audience,
            tone=body.tone,
            language=body.language,
            channels=body.channels,
        ),
    )

    batch_id = str(uuid4())
    posts = [
        DraftPostRecord(
            post_id=str(uuid4()),
            channel=v.channel,
            text=v.text,
            hashtags=v.hashtags,
        )
        for v in result.output.variants
    ]

    batch = DraftBatchRecord(
        batch_id=batch_id,
        agent_id=body.agent_id,
        customer_id=body.customer_id,
        theme=result.output.canonical.theme,
        brand_name=body.brand_name,
        created_at=datetime.utcnow(),
        posts=posts,
    )

    store.save_batch(batch)
    return CreateDraftBatchResponse(**batch.model_dump())
