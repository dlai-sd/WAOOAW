"""Usage events (append-only).

Goal 4: provide an auditable usage ledger schema that can be persisted.

This initial implementation is in-memory (unit-test friendly). Later phases can
swap this for Postgres/Redis without changing API handlers.
"""

from __future__ import annotations

import os
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Protocol, Tuple

from pydantic import BaseModel, Field


class UsageEventType(str, Enum):
    SKILL_EXECUTION = "skill_execution"
    BUDGET_PRECHECK = "budget_precheck"
    PUBLISH_ACTION = "publish_action"


class UsageEvent(BaseModel):
    event_type: UsageEventType

    # Correlation & ownership
    correlation_id: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    agent_id: Optional[str] = None

    # Classification
    purpose: Optional[str] = None
    model: Optional[str] = None
    cache_hit: bool = False

    # Metering primitives (LLM-front-door compatible)
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class UsageEventStore(Protocol):
    def append(self, event: UsageEvent) -> None:
        ...

    def list_events(
        self,
        *,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        event_type: Optional[UsageEventType] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[UsageEvent]:
        ...


class InMemoryUsageEventStore:
    def __init__(self) -> None:
        self._events: List[UsageEvent] = []

    def append(self, event: UsageEvent) -> None:
        self._events.append(event)

    def list_events(
        self,
        *,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        event_type: Optional[UsageEventType] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[UsageEvent]:
        filtered = _filter_events(
            self._events,
            customer_id=customer_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
            event_type=event_type,
            since=since,
            until=until,
            limit=limit,
        )
        return list(filtered)


class FileUsageEventStore:
    """Append-only JSONL store.

    This intentionally avoids DB migrations; it provides a persistence primitive
    for development/demo environments and can be swapped for Redis/Postgres
    later behind the same interface.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, event: UsageEvent) -> None:
        line = event.model_dump_json()
        with open(self._path, "a", encoding="utf-8") as f:
            _flock_exclusive(f)
            f.write(line)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
            _flock_release(f)

    def list_events(
        self,
        *,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        event_type: Optional[UsageEventType] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[UsageEvent]:
        since_n = _normalize_dt(since)
        until_n = _normalize_dt(until)

        if limit is not None and limit <= 0:
            return []

        collected: List[UsageEvent] | Deque[UsageEvent]
        if limit is None:
            collected = []
        else:
            collected = deque(maxlen=limit)

        with open(self._path, "r", encoding="utf-8") as f:
            _flock_shared(f)
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                event = UsageEvent.model_validate_json(raw)
                if not _event_matches(
                    event,
                    customer_id=customer_id,
                    agent_id=agent_id,
                    correlation_id=correlation_id,
                    event_type=event_type,
                    since=since_n,
                    until=until_n,
                ):
                    continue
                collected.append(event)
            _flock_release(f)

        return list(collected)


class UsageAggregateBucket(str, Enum):
    DAY = "day"
    MONTH = "month"


class UsageAggregateRow(BaseModel):
    bucket: UsageAggregateBucket
    bucket_start: datetime
    customer_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_type: Optional[UsageEventType] = None

    event_count: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


def aggregate_usage_events(
    events: Iterable[UsageEvent],
    *,
    bucket: UsageAggregateBucket = UsageAggregateBucket.DAY,
) -> List[UsageAggregateRow]:
    """Aggregate events into day/month buckets.

    Groups by (bucket_start, customer_id, agent_id, event_type).
    """

    def bucket_start(dt: datetime) -> datetime:
        dt = _normalize_dt(dt) or dt
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if bucket == UsageAggregateBucket.DAY:
            return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
        return datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)

    grouped: Dict[Tuple[datetime, Optional[str], Optional[str], Optional[UsageEventType]], UsageAggregateRow] = {}
    for e in events:
        start = bucket_start(e.created_at)
        key = (start, e.customer_id, e.agent_id, e.event_type)
        row = grouped.get(key)
        if row is None:
            row = UsageAggregateRow(
                bucket=bucket,
                bucket_start=start,
                customer_id=e.customer_id,
                agent_id=e.agent_id,
                event_type=e.event_type,
                event_count=0,
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
            )
            grouped[key] = row
        row.event_count += 1
        row.tokens_in += int(e.tokens_in)
        row.tokens_out += int(e.tokens_out)
        row.cost_usd += float(e.cost_usd)

    return sorted(grouped.values(), key=lambda r: (r.bucket_start, r.customer_id or "", r.agent_id or "", r.event_type or ""))


def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _event_matches(
    event: UsageEvent,
    *,
    customer_id: Optional[str],
    agent_id: Optional[str],
    correlation_id: Optional[str],
    event_type: Optional[UsageEventType],
    since: Optional[datetime],
    until: Optional[datetime],
) -> bool:
    if customer_id is not None and event.customer_id != customer_id:
        return False
    if agent_id is not None and event.agent_id != agent_id:
        return False
    if correlation_id is not None and event.correlation_id != correlation_id:
        return False
    if event_type is not None and event.event_type != event_type:
        return False

    created = _normalize_dt(event.created_at) or event.created_at
    if since is not None and created < since:
        return False
    if until is not None and created > until:
        return False
    return True


def _filter_events(
    events: Iterable[UsageEvent],
    *,
    customer_id: Optional[str],
    agent_id: Optional[str],
    correlation_id: Optional[str],
    event_type: Optional[UsageEventType],
    since: Optional[datetime],
    until: Optional[datetime],
    limit: Optional[int],
) -> Iterable[UsageEvent]:
    since_n = _normalize_dt(since)
    until_n = _normalize_dt(until)

    filtered = [
        e
        for e in events
        if _event_matches(
            e,
            customer_id=customer_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
            event_type=event_type,
            since=since_n,
            until=until_n,
        )
    ]
    if limit is None:
        return filtered
    if limit <= 0:
        return []
    return filtered[-limit:]


def _flock_exclusive(f) -> None:  # type: ignore[no-untyped-def]
    try:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except Exception:
        return


def _flock_shared(f) -> None:  # type: ignore[no-untyped-def]
    try:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
    except Exception:
        return


def _flock_release(f) -> None:  # type: ignore[no-untyped-def]
    try:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return
