from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.router import api_v1_router
from api.v1.agent_mold import get_usage_event_store
from core.exceptions import PolicyEnforcementError, UsageLimitError
from main import policy_enforcement_error_handler, usage_limit_error_handler
from services.usage_events import InMemoryUsageEventStore, UsageEvent, UsageEventType


def _make_test_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(PolicyEnforcementError, policy_enforcement_error_handler)
    app.add_exception_handler(UsageLimitError, usage_limit_error_handler)

    store = InMemoryUsageEventStore()
    app.dependency_overrides[get_usage_event_store] = lambda: store

    app.include_router(api_v1_router)
    return app


@pytest.mark.asyncio
async def test_list_usage_events_filters_and_limit():
    app = _make_test_app()
    store = app.dependency_overrides[get_usage_event_store]()

    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    store.append(
        UsageEvent(
            event_type=UsageEventType.BUDGET_PRECHECK,
            correlation_id="corr-1",
            customer_id="CUST-1",
            agent_id="AGT-1",
            purpose="demo",
            model="gpt-test",
            cache_hit=False,
            tokens_in=10,
            tokens_out=20,
            cost_usd=0.01,
            created_at=t0,
        )
    )
    store.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-2",
            customer_id="CUST-1",
            agent_id="AGT-1",
            purpose="demo",
            action="draft",
            model="gpt-test",
            cache_hit=True,
            tokens_in=1,
            tokens_out=2,
            cost_usd=0.02,
            created_at=t0,
        )
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/usage-events",
            params={
                "customer_id": "CUST-1",
                "agent_id": "AGT-1",
                "limit": 1,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1

    last = body["events"][0]
    assert last["correlation_id"] == "corr-2"
    assert last["event_type"] == "skill_execution"
    assert last["tokens_in"] == 1
    assert last["tokens_out"] == 2
    assert last["cost_usd"] == 0.02
    assert last["cache_hit"] is True
    assert last["purpose"] == "demo"
    assert last["action"] == "draft"
    assert last["model"] == "gpt-test"


@pytest.mark.asyncio
async def test_usage_events_aggregate_day_bucket():
    app = _make_test_app()
    store = app.dependency_overrides[get_usage_event_store]()

    day = datetime(2026, 1, 2, 8, 30, tzinfo=timezone.utc)
    store.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-1",
            customer_id="CUST-1",
            agent_id="AGT-1",
            tokens_in=10,
            tokens_out=5,
            cost_usd=0.5,
            created_at=day,
        )
    )
    store.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id="corr-2",
            customer_id="CUST-1",
            agent_id="AGT-1",
            tokens_in=20,
            tokens_out=15,
            cost_usd=1.5,
            created_at=day,
        )
    )
    store.append(
        UsageEvent(
            event_type=UsageEventType.BUDGET_PRECHECK,
            correlation_id="corr-3",
            customer_id="CUST-1",
            agent_id="AGT-1",
            cost_usd=0.0,
            created_at=day,
        )
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/usage-events/aggregate",
            params={
                "bucket": "day",
                "customer_id": "CUST-1",
                "agent_id": "AGT-1",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2

    rows = body["rows"]
    skill = next(r for r in rows if r["event_type"] == "skill_execution")
    assert skill["event_count"] == 2
    assert skill["tokens_in"] == 30
    assert skill["tokens_out"] == 20
    assert skill["cost_usd"] == 2.0

    budget = next(r for r in rows if r["event_type"] == "budget_precheck")
    assert budget["event_count"] == 1
    assert budget["cost_usd"] == 0.0
