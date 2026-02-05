"""Usage events read endpoints.

Goal 4 / Epic 4.1:
- Provide a minimal API surface to list usage events and retrieve day/month
  aggregates so PP/CP can render usage dashboards.

This router is intentionally read-only and relies on the UsageEventStore
configured via the Agent Mold module (in-memory by default, JSONL optional).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.v1.agent_mold import get_usage_event_store
from services.usage_events import (
    UsageAggregateBucket,
    UsageAggregateRow,
    UsageEvent,
    UsageEventStore,
    UsageEventType,
    aggregate_usage_events,
)


router = APIRouter(prefix="/usage-events", tags=["usage-events"])


class UsageEventsListResponse(BaseModel):
    count: int
    events: List[Dict[str, Any]]


@router.get("", response_model=UsageEventsListResponse)
async def list_usage_events(
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    event_type: Optional[UsageEventType] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    store: UsageEventStore = Depends(get_usage_event_store),
) -> UsageEventsListResponse:
    events: List[UsageEvent] = store.list_events(
        customer_id=customer_id,
        agent_id=agent_id,
        correlation_id=correlation_id,
        event_type=event_type,
        since=since,
        until=until,
        limit=limit,
    )

    return UsageEventsListResponse(
        count=len(events),
        events=[e.model_dump(mode="json") for e in events],
    )


class UsageEventsAggregateResponse(BaseModel):
    count: int
    rows: List[UsageAggregateRow]


@router.get("/aggregate", response_model=UsageEventsAggregateResponse)
async def aggregate_usage_events_endpoint(
    bucket: UsageAggregateBucket = UsageAggregateBucket.DAY,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    event_type: Optional[UsageEventType] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    store: UsageEventStore = Depends(get_usage_event_store),
) -> UsageEventsAggregateResponse:
    events: List[UsageEvent] = store.list_events(
        customer_id=customer_id,
        agent_id=agent_id,
        correlation_id=correlation_id,
        event_type=event_type,
        since=since,
        until=until,
        limit=None,
    )
    rows = aggregate_usage_events(events, bucket=bucket)

    return UsageEventsAggregateResponse(count=len(rows), rows=rows)
