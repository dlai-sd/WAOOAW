from datetime import datetime, timezone

from services.usage_events import (
    FileUsageEventStore,
    InMemoryUsageEventStore,
    UsageAggregateBucket,
    UsageEvent,
    UsageEventType,
    aggregate_usage_events,
)


def test_usage_event_store_appends_and_lists():
    store = InMemoryUsageEventStore()

    store.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-1",
            customer_id="CUST-1",
            agent_id="AGT-1",
            purpose="demo",
            model=None,
            cache_hit=False,
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
        )
    )

    events = store.list_events()
    assert len(events) == 1
    assert events[0].event_type == UsageEventType.SKILL_EXECUTION
    assert events[0].correlation_id == "corr-1"


def test_file_usage_event_store_persists(tmp_path):
    path = tmp_path / "usage_events.jsonl"

    store = FileUsageEventStore(path)
    store.append(
        UsageEvent(
            event_type=UsageEventType.BUDGET_PRECHECK,
            correlation_id="corr-1",
            customer_id="CUST-1",
            agent_id="AGT-1",
            cost_usd=0.0,
        )
    )
    store.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-2",
            customer_id="CUST-1",
            agent_id="AGT-1",
            cost_usd=1.23,
        )
    )

    # New instance should see persisted events.
    store2 = FileUsageEventStore(path)
    events = store2.list_events(customer_id="CUST-1")
    assert len(events) == 2

    last = store2.list_events(customer_id="CUST-1", limit=1)
    assert len(last) == 1
    assert last[0].correlation_id == "corr-2"


def test_aggregate_usage_events_day_bucket():
    day = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    events = [
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-1",
            customer_id="CUST-1",
            agent_id="AGT-1",
            tokens_in=10,
            tokens_out=5,
            cost_usd=0.5,
            created_at=day,
        ),
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-2",
            customer_id="CUST-1",
            agent_id="AGT-1",
            tokens_in=20,
            tokens_out=15,
            cost_usd=1.5,
            created_at=day,
        ),
        UsageEvent(
            event_type=UsageEventType.BUDGET_PRECHECK,
            correlation_id="corr-3",
            customer_id="CUST-1",
            agent_id="AGT-1",
            cost_usd=0.0,
            created_at=day,
        ),
    ]

    rows = aggregate_usage_events(events, bucket=UsageAggregateBucket.DAY)
    # Two rows: one per event_type.
    assert len(rows) == 2

    skill = next(r for r in rows if r.event_type == UsageEventType.SKILL_EXECUTION)
    assert skill.event_count == 2
    assert skill.tokens_in == 30
    assert skill.tokens_out == 20
    assert skill.cost_usd == 2.0
