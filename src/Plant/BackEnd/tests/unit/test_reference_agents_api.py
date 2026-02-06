from fastapi import FastAPI
import pytest
from httpx import ASGITransport, AsyncClient

from api.v1.router import api_v1_router
from core.exceptions import PolicyEnforcementError, UsageLimitError
from main import policy_enforcement_error_handler, usage_limit_error_handler
from api.v1.agent_mold import get_usage_ledger, get_usage_event_store
from services.usage_ledger import InMemoryUsageLedger
from services.usage_events import InMemoryUsageEventStore


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


@pytest.mark.asyncio
async def test_list_reference_agents():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/reference-agents")

    assert resp.status_code == 200
    agents = resp.json()
    assert isinstance(agents, list)
    assert {a["agent_id"] for a in agents} >= {
        "AGT-MKT-BEAUTY-001",
        "AGT-MKT-CAKE-001",
        "AGT-TUTOR-WB-001",
        "AGT-TRD-DELTA-001",
    }


@pytest.mark.asyncio
async def test_run_marketing_reference_agent_drafts_successfully():
    app = _make_test_app()
    transport = ASGITransport(app=app)
    store = app.dependency_overrides[get_usage_event_store]()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
            json={
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "estimated_cost_usd": 0.1,
                "meter_tokens_in": 11,
                "meter_tokens_out": 22,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_id"] == "AGT-MKT-CAKE-001"
    assert body["published"] is False
    assert body["status"] == "draft"
    assert body["draft"]["output"]["canonical"]["core_message"]

    events = store.list_events(agent_id="AGT-MKT-CAKE-001")
    assert any(e.event_type == "skill_execution" for e in events)


@pytest.mark.asyncio
async def test_run_marketing_reference_agent_publish_requires_approval():
    app = _make_test_app()
    transport = ASGITransport(app=app)
    store = app.dependency_overrides[get_usage_event_store]()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post(
            "/api/v1/reference-agents/AGT-MKT-BEAUTY-001/run",
            json={
                "customer_id": "CUST-1",
                "do_publish": True,
                "theme": "Valentine campaign",
            },
        )

        allowed = await client.post(
            "/api/v1/reference-agents/AGT-MKT-BEAUTY-001/run",
            json={
                "customer_id": "CUST-1",
                "do_publish": True,
                "approval_id": "APR-123",
                "theme": "Valentine campaign",
            },
        )

    assert denied.status_code == 403
    assert denied.json()["reason"] == "approval_required"

    assert allowed.status_code == 200
    allowed_body = allowed.json()
    assert allowed_body["published"] is True
    assert allowed_body["status"] == "published"

    events = store.list_events(agent_id="AGT-MKT-BEAUTY-001")
    assert any(e.event_type == "publish_action" for e in events)


@pytest.mark.asyncio
async def test_run_marketing_reference_agent_publish_requires_approval_for_cake_agent():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post(
            "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
            json={
                "customer_id": "CUST-1",
                "do_publish": True,
            },
        )

    assert denied.status_code == 403
    assert denied.json()["reason"] == "approval_required"


@pytest.mark.asyncio
async def test_run_tutor_reference_agent_returns_lesson_plan():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TUTOR-WB-001/run",
            json={
                "customer_id": "CUST-1",
                "topic": "Triangles",
                "meter_tokens_in": 10,
                "meter_tokens_out": 20,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_type"] == "tutor"
    assert body["draft"]["topic"] == "Triangles"
    assert len(body["draft"]["whiteboard_steps"]) >= 1
    assert len(body["draft"]["quiz_questions"]) >= 2
    assert isinstance(body["draft"].get("ui_event_stream"), list)
    assert any(e.get("type") == "whiteboard_step" for e in body["draft"]["ui_event_stream"])
    assert any(e.get("type") == "quiz_question" for e in body["draft"]["ui_event_stream"])


@pytest.mark.asyncio
async def test_run_marketing_reference_agent_enters_in_review_when_approval_id_provided():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
            json={
                "customer_id": "CUST-1",
                "approval_id": "APR-123",
                "theme": "Valentine campaign",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["published"] is False
    assert body["status"] == "in_review"
    assert body["review"]["approval_id"] == "APR-123"


@pytest.mark.asyncio
async def test_trial_blocks_publish_for_reference_agents():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
            json={
                "customer_id": "CUST-1",
                "trial_mode": True,
                "do_publish": True,
                "approval_id": "APR-123",
            },
        )

    assert resp.status_code == 429
    assert resp.json()["reason"] == "trial_production_write_blocked"


@pytest.mark.asyncio
async def test_trade_intent_contract_requires_required_fields():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
            },
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_trade_intent_contract_rejects_invalid_fields():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "BTC",
                "units": -1,
                "side": "buy",
                "action": "open",
                "market": False,
            },
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_trade_intent_contract_forbids_extra_fields_like_raw_keys():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "BTC",
                "units": 1,
                "side": "long",
                "action": "enter",
                "market": True,
                "api_key": "SHOULD-NOT-BE-ACCEPTED",
            },
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_trade_intent_contract_accepts_valid_payload_and_returns_draft_plan():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "btc",
                "units": 2,
                "side": "long",
                "action": "enter",
                "market": True,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_id"] == "AGT-TRD-DELTA-001"
    assert body["agent_type"] == "trading"
    assert body["status"] == "draft"
    assert body["draft"]["coin"] == "BTC"


@pytest.mark.asyncio
async def test_trading_intent_action_requires_approval_id_for_side_effects():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "btc",
                "units": 2,
                "side": "long",
                "action": "enter",
                "market": True,
                "intent_action": "place_order",
            },
            headers={"X-Correlation-ID": "cid-trd-ia-1"},
        )

    assert resp.status_code == 403
    body = resp.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"
    assert body["correlation_id"] == "cid-trd-ia-1"


@pytest.mark.asyncio
async def test_trading_intent_action_allows_with_approval_id_and_is_echoed_in_draft():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "btc",
                "units": 2,
                "side": "long",
                "action": "enter",
                "market": True,
                "intent_action": "close_position",
                "approval_id": "APR-123",
            },
            headers={"X-Correlation-ID": "cid-trd-ia-2"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_type"] == "trading"
    assert body["draft"]["intent_action"] == "close_position"
    assert body["draft"]["approval_id"] == "APR-123"


@pytest.mark.asyncio
async def test_trading_intent_action_rejects_unknown_values():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/reference-agents/AGT-TRD-DELTA-001/run",
            json={
                "customer_id": "CUST-1",
                "exchange_account_id": "EXCH-1",
                "coin": "btc",
                "units": 2,
                "side": "long",
                "action": "enter",
                "market": True,
                "intent_action": "publish",
            },
        )

    assert resp.status_code == 422
