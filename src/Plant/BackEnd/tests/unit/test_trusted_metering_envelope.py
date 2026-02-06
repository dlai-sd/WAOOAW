from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
import pytest
from httpx import ASGITransport, AsyncClient

from api.v1.router import api_v1_router
from core.exceptions import PolicyEnforcementError, UsageLimitError
from main import policy_enforcement_error_handler, usage_limit_error_handler
from api.v1.agent_mold import get_usage_ledger, get_usage_event_store
from services.usage_ledger import InMemoryUsageLedger
from services.usage_events import InMemoryUsageEventStore
from services.metering import sign_trusted_metering_envelope


def _make_test_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(PolicyEnforcementError, policy_enforcement_error_handler)
    app.add_exception_handler(UsageLimitError, usage_limit_error_handler)

    ledger = InMemoryUsageLedger()
    store = InMemoryUsageEventStore()
    app.dependency_overrides[get_usage_ledger] = lambda: ledger
    app.dependency_overrides[get_usage_event_store] = lambda: store

    app.include_router(api_v1_router)
    return app


def _trusted_headers(*, secret: str, correlation_id: str) -> dict[str, str]:
    ts = int(datetime.now(tz=timezone.utc).timestamp())
    tokens_in = 100
    tokens_out = 50
    model = "gpt-4o-mini"
    cache_hit = False
    cost_usd = 0.123456

    sig = sign_trusted_metering_envelope(
        secret=secret,
        timestamp=ts,
        correlation_id=correlation_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model=model,
        cache_hit=cache_hit,
        cost_usd=cost_usd,
    )

    return {
        "X-Metering-Timestamp": str(ts),
        "X-Metering-Tokens-In": str(tokens_in),
        "X-Metering-Tokens-Out": str(tokens_out),
        "X-Metering-Model": model,
        "X-Metering-Cache-Hit": "0",
        "X-Metering-Cost-USD": str(cost_usd),
        "X-Metering-Signature": sig,
    }


@pytest.mark.asyncio
async def test_budgeted_skill_execution_requires_trusted_metering_envelope(monkeypatch):
    import services.metering as metering

    monkeypatch.setenv("METERING_ENVELOPE_SECRET", "test-secret")
    monkeypatch.setattr(metering, "get_query_budget_monthly_usd", lambda _: 10.0)

    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_budgeted",
                "correlation_id": "corr-1",
                "estimated_cost_usd": 0.5,
                "meter_tokens_in": 999,
                "meter_tokens_out": 999,
                "meter_model": "spoofed",
                "theme": "Launch",
                "brand_name": "Cake Shop",
            },
        )

    assert resp.status_code == 429
    body = resp.json()
    assert body["reason"] == "metering_envelope_required"


@pytest.mark.asyncio
async def test_budgeted_skill_execution_accepts_valid_trusted_metering_envelope(monkeypatch):
    import services.metering as metering

    secret = "test-secret"
    monkeypatch.setenv("METERING_ENVELOPE_SECRET", secret)
    monkeypatch.setattr(metering, "get_query_budget_monthly_usd", lambda _: 10.0)

    app = _make_test_app()
    transport = ASGITransport(app=app)
    store = app.dependency_overrides[get_usage_event_store]()

    headers = _trusted_headers(secret=secret, correlation_id="corr-2")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            headers=headers,
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_budgeted",
                "correlation_id": "corr-2",
                # Spoofed body values should be ignored in favor of the trusted envelope.
                "estimated_cost_usd": 9.0,
                "meter_tokens_in": 0,
                "meter_tokens_out": 0,
                "meter_model": "spoofed",
                "meter_cache_hit": True,
                "theme": "Launch",
                "brand_name": "Cake Shop",
            },
        )

    assert resp.status_code == 200

    events = store.list_events(agent_id="AGT-1")
    skill_events = [e for e in events if e.event_type == "skill_execution"]
    assert skill_events, "expected a skill_execution usage event"
    last = skill_events[-1]

    assert last.tokens_in == 100
    assert last.tokens_out == 50
    assert last.model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_budgeted_reference_agent_requires_trusted_metering_envelope(monkeypatch):
    import services.metering as metering

    monkeypatch.setenv("METERING_ENVELOPE_SECRET", "test-secret")
    monkeypatch.setattr(metering, "get_query_budget_monthly_usd", lambda _: 10.0)

    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TUTOR-WB-001/run",
            json={
                "customer_id": "CUST-1",
                "plan_id": "plan_budgeted",
                "correlation_id": "corr-3",
                "topic": "Triangles",
                "meter_tokens_in": 10,
                "meter_tokens_out": 20,
            },
        )

    assert resp.status_code == 429
    body = resp.json()
    assert body["reason"] == "metering_envelope_required"
