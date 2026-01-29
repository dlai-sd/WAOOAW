from fastapi import FastAPI
import pytest
from httpx import ASGITransport, AsyncClient

from api.v1.router import api_v1_router
from core.exceptions import PolicyEnforcementError
from main import policy_enforcement_error_handler
from core.exceptions import UsageLimitError
from main import usage_limit_error_handler
from api.v1.agent_mold import get_usage_ledger
from services.usage_ledger import InMemoryUsageLedger
from api.v1.agent_mold import get_usage_event_store
from services.usage_events import InMemoryUsageEventStore


def _make_test_app() -> FastAPI:
    # Keep this unit-test-only: avoid `main.py` startup DB initialization.
    app = FastAPI()
    app.add_exception_handler(PolicyEnforcementError, policy_enforcement_error_handler)
    app.add_exception_handler(UsageLimitError, usage_limit_error_handler)

    # Isolate metering state across tests, but keep it stable across requests.
    ledger = InMemoryUsageLedger()
    app.dependency_overrides[get_usage_ledger] = lambda: ledger

    event_store = InMemoryUsageEventStore()
    app.dependency_overrides[get_usage_event_store] = lambda: event_store

    app.include_router(api_v1_router)
    return app


@pytest.mark.asyncio
async def test_enforce_tool_use_denies_publish_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={"agent_id": "AGT-1", "action": "publish", "payload": {}},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["status"] == 403
    assert body["reason"] == "approval_required"


@pytest.mark.asyncio
async def test_enforce_tool_use_allows_publish_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={
                "agent_id": "AGT-1",
                "action": "publish",
                "payload": {},
                "approval_id": "APR-123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True


@pytest.mark.asyncio
async def test_skill_execution_denies_publish_intent_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "intent_action": "publish",
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"


@pytest.mark.asyncio
async def test_skill_execution_allows_publish_intent_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "intent_action": "publish",
                "approval_id": "APR-123",
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["playbook_id"]
    assert body["output"]["canonical"]["core_message"]
    assert len(body["output"]["variants"]) == 2


@pytest.mark.asyncio
async def test_trial_daily_task_cap_blocks_after_10():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(10):
            ok = await client.post(
                "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
                json={
                    "agent_id": "AGT-1",
                    "trial_mode": True,
                    "customer_id": "CUST-1",
                    "theme": "Grand opening",
                    "brand_name": "Cake Shop",
                },
            )
            assert ok.status_code == 200

        blocked = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "trial_mode": True,
                "customer_id": "CUST-1",
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["title"] == "Usage Limit Denied"
    assert body["reason"] == "trial_daily_cap"


@pytest.mark.asyncio
async def test_trial_blocks_production_write_intent_even_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "trial_mode": True,
                "customer_id": "CUST-1",
                "intent_action": "publish",
                "approval_id": "APR-123",
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 429
    body = response.json()
    assert body["title"] == "Usage Limit Denied"
    assert body["reason"] == "trial_production_write_blocked"


@pytest.mark.asyncio
async def test_trial_blocks_high_cost_call_over_one_usd():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "trial_mode": True,
                "customer_id": "CUST-1",
                "estimated_cost_usd": 1.01,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 429
    body = response.json()
    assert body["title"] == "Usage Limit Denied"
    assert body["reason"] == "trial_high_cost_call"


@pytest.mark.asyncio
async def test_monthly_budget_blocks_when_estimated_cost_exceeds_plan_budget():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "estimated_cost_usd": 6.0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert ok.status_code == 200

        blocked = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "estimated_cost_usd": 6.0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["title"] == "Usage Limit Denied"
    assert body["reason"] == "monthly_budget_exceeded"


@pytest.mark.asyncio
async def test_monthly_budget_can_use_token_based_cost_estimate(monkeypatch):
    # Starter plan budget is $10 in the template. Set a pricing where 10k input tokens = $10.
    monkeypatch.setenv(
        "MODEL_PRICING_JSON",
        '{"mock-model": {"input_per_1k": 1.0, "output_per_1k": 0.0}}',
    )

    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "meter_model": "mock-model",
                "meter_tokens_in": 1000,
                "meter_tokens_out": 0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert ok.status_code == 200

        # Second call spends another $9 via tokens => total would be $10 (allowed) then $11 (blocked)
        ok2 = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "meter_model": "mock-model",
                "meter_tokens_in": 9000,
                "meter_tokens_out": 0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert ok2.status_code == 200

        blocked = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "meter_model": "mock-model",
                "meter_tokens_in": 1000,
                "meter_tokens_out": 0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert blocked.status_code == 429

    body = blocked.json()
    assert body["reason"] == "monthly_budget_exceeded"


@pytest.mark.asyncio
async def test_usage_events_recorded_on_success_and_not_on_budget_deny():
    app = _make_test_app()
    transport = ASGITransport(app=app)

    # Reach into the overridden store instance.
    store = app.dependency_overrides[get_usage_event_store]()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "estimated_cost_usd": 1.0,
                "meter_tokens_in": 11,
                "meter_tokens_out": 22,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert ok.status_code == 200

        # Force a deny by trying to exceed the remaining monthly budget.
        denied = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                "estimated_cost_usd": 999.0,
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )
        assert denied.status_code == 429

    events = store.list_events()
    # Expect exactly one skill_execution event (denied request should not create one).
    skill_events = [e for e in events if e.event_type == "skill_execution"]
    assert len(skill_events) == 1
    assert skill_events[0].tokens_in == 11
    assert skill_events[0].tokens_out == 22


@pytest.mark.asyncio
async def test_execute_skill_denies_publish_intent_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "intent_action": "publish",
                "theme": "Valentine campaign",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"


@pytest.mark.asyncio
async def test_execute_skill_allows_publish_intent_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-1",
                "intent_action": "publish",
                "approval_id": "APR-123",
                "theme": "Valentine campaign",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["playbook_id"]
    assert body["output"]["canonical"]["core_message"]
    assert len(body["output"]["variants"]) >= 2
