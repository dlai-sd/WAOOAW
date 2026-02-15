from fastapi import FastAPI
import pytest
from httpx import ASGITransport, AsyncClient

from api.v1.router import api_v1_router
from core.exceptions import PolicyEnforcementError
from main import policy_enforcement_error_handler
from core.exceptions import UsageLimitError
from main import usage_limit_error_handler
from api.v1.agent_mold import get_usage_ledger
from api.v1.agent_mold import MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY
from services.usage_ledger import InMemoryUsageLedger
from api.v1.agent_mold import get_usage_event_store
from services.usage_events import InMemoryUsageEventStore
from services.policy_denial_audit import InMemoryPolicyDenialAuditStore
from services.policy_denial_audit import get_policy_denial_audit_store
from api.v1 import agent_types_simple


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

    policy_store = InMemoryPolicyDenialAuditStore()
    app.dependency_overrides[get_policy_denial_audit_store] = lambda: policy_store

    app.include_router(api_v1_router)
    return app


@pytest.fixture(autouse=True)
def _patch_marketing_agent_type_required_skill_keys():
    """SK-3.3 requires skill execution to be allowlisted by agent type."""

    key = "marketing.digital_marketing.v1"
    original = agent_types_simple._DEFINITIONS[key]
    agent_types_simple._DEFINITIONS[key] = original.model_copy(
        update={"required_skill_keys": [MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY]}
    )
    try:
        yield
    finally:
        agent_types_simple._DEFINITIONS[key] = original


@pytest.mark.asyncio
async def test_enforce_tool_use_denies_publish_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={"agent_id": "AGT-MKT-HEALTH-001", "action": "publish", "payload": {}},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["status"] == 403
    assert body["reason"] == "approval_required"
    assert body["details"]["decision_id"]


@pytest.mark.asyncio
async def test_policy_denial_is_persisted_and_listable_via_audit_endpoint():
    app = _make_test_app()
    transport = ASGITransport(app=app)

    # Reach into the overridden store instance.
    store = app.dependency_overrides[get_policy_denial_audit_store]()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={"agent_id": "AGT-MKT-HEALTH-001", "action": "publish", "payload": {}},
        )
        assert denied.status_code == 403

        audit = await client.get("/api/v1/audit/policy-denials?limit=10")
        assert audit.status_code == 200
        payload = audit.json()

    assert payload["count"] >= 1
    assert len(store.list_records(limit=10)) >= 1
    last = payload["records"][-1]
    assert last["action"] == "publish"
    assert last["reason"] in {"approval_required", "autopublish_not_allowed"}
    assert last["decision_id"]


@pytest.mark.asyncio
async def test_enforce_tool_use_allows_publish_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={
                "agent_id": "AGT-MKT-HEALTH-001",
                "action": "publish",
                "payload": {},
                "approval_id": "APR-123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True


@pytest.mark.asyncio
async def test_enforce_tool_use_denies_trading_actions_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={"agent_id": "AGT-TRD-DELTA-001", "action": "place_order", "payload": {}},
            headers={"X-Correlation-ID": "cid-trd-1"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"
    assert body["correlation_id"] == "cid-trd-1"


@pytest.mark.asyncio
async def test_enforce_tool_use_allows_trading_actions_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/tool-use",
            json={
                "agent_id": "AGT-TRD-DELTA-001",
                "action": "close_position",
                "payload": {},
                "approval_id": "APR-789",
            },
            headers={"X-Correlation-ID": "cid-trd-2"},
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
                "agent_id": "AGT-MKT-HEALTH-001",
                "intent_action": "publish",
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"
    assert body["details"]["decision_id"]


@pytest.mark.asyncio
async def test_skill_execution_allows_publish_intent_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-MKT-HEALTH-001",
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
    assert len(body["output"]["variants"]) == 5


@pytest.mark.asyncio
async def test_skill_execution_denies_when_skill_not_allowlisted_for_agent_type():
    key = "marketing.digital_marketing.v1"
    original = agent_types_simple._DEFINITIONS[key]
    agent_types_simple._DEFINITIONS[key] = original.model_copy(update={"required_skill_keys": []})
    try:
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
                json={
                    "agent_id": "AGT-MKT-HEALTH-001",
                    "theme": "Grand opening",
                    "brand_name": "Cake Shop",
                },
            )
    finally:
        agent_types_simple._DEFINITIONS[key] = original

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "skill_not_allowed"


@pytest.mark.asyncio
async def test_trial_daily_task_cap_blocks_after_10():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(10):
            ok = await client.post(
                "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
                json={
                    "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
async def test_monthly_budget_fails_closed_when_plan_id_set_but_no_metering():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-MKT-HEALTH-001",
                "customer_id": "CUST-1",
                "plan_id": "plan_starter",
                # No estimated_cost_usd and no meter_* => effective cost would be 0
                "theme": "Grand opening",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 429
    body = response.json()
    assert body["title"] == "Usage Limit Denied"
    assert body["reason"] == "metering_required_for_budget"


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
                "agent_id": "AGT-MKT-HEALTH-001",
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
                "agent_id": "AGT-MKT-HEALTH-001",
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
    async def test_reference_agent_denies_publish_without_approval_id():
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
                json={
                    "customer_id": "CUST-1",
                    "plan_id": "plan_starter",
                    "estimated_cost_usd": 0.01,
                    "do_publish": True,
                },
            )

        assert response.status_code == 403
        body = response.json()
        assert body["title"] == "Policy Enforcement Denied"
        assert body["reason"] == "approval_required"

    @pytest.mark.asyncio
    async def test_reference_agent_allows_publish_with_approval_id():
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
                json={
                    "customer_id": "CUST-1",
                    "plan_id": "plan_starter",
                    "estimated_cost_usd": 0.01,
                    "do_publish": True,
                    "approval_id": "APR-123",
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["published"] is True
        assert body["draft"]

    @pytest.mark.asyncio
    async def test_reference_agent_trial_blocks_publish_even_with_approval_id():
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
                json={
                    "trial_mode": True,
                    "customer_id": "CUST-1",
                    "plan_id": "plan_starter",
                    "estimated_cost_usd": 0.01,
                    "do_publish": True,
                    "approval_id": "APR-123",
                },
            )

        assert response.status_code == 429
        body = response.json()
        assert body["title"] == "Usage Limit Denied"
        assert body["reason"] == "trial_production_write_blocked"


    @pytest.mark.asyncio
    async def test_reference_agent_autopublish_denied_by_default():
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
                json={
                    "customer_id": "CUST-1",
                    "plan_id": "plan_starter",
                    "estimated_cost_usd": 0.01,
                    "autopublish": True,
                    "approval_id": "APR-123",
                },
            )

        assert response.status_code == 403
        body = response.json()
        assert body["title"] == "Policy Enforcement Denied"
        assert body["reason"] == "autopublish_not_allowed"


    @pytest.mark.asyncio
    async def test_reference_agent_autopublish_allowed_when_enabled_in_spec(monkeypatch):
        from agent_mold.reference_agents import get_reference_agent as real_get
        from agent_mold.spec import DimensionName

        agent = real_get("AGT-MKT-CAKE-001")
        assert agent is not None

        spec2 = agent.spec.model_copy(deep=True)
        skill_dim = spec2.dimensions[DimensionName.SKILL]
        skill_dim.config["autopublish_allowed"] = True

        agent2 = type(agent)(
            agent_id=agent.agent_id,
            display_name=agent.display_name,
            agent_type=agent.agent_type,
            spec=spec2,
            defaults=agent.defaults,
        )

        import api.v1.reference_agents as ref_api

        monkeypatch.setattr(ref_api, "get_reference_agent", lambda _agent_id: agent2)

        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/reference-agents/AGT-MKT-CAKE-001/run",
                json={
                    "customer_id": "CUST-1",
                    "plan_id": "plan_starter",
                    "estimated_cost_usd": 0.01,
                    "autopublish": True,
                    "approval_id": "APR-123",
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["published"] is True


    @pytest.mark.asyncio
    async def test_skill_execution_autopublish_denied_for_unknown_agent():
        transport = ASGITransport(app=_make_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
                json={
                    "agent_id": "AGT-UNKNOWN",
                    "autopublish": True,
                    "approval_id": "APR-123",
                    "theme": "Grand opening",
                    "brand_name": "Cake Shop",
                },
            )

        assert response.status_code == 403
        body = response.json()
        assert body["title"] == "Policy Enforcement Denied"
        assert body["reason"] == "autopublish_not_allowed"


@pytest.mark.asyncio
async def test_execute_skill_denies_publish_intent_without_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-MKT-HEALTH-001",
                "intent_action": "publish",
                "theme": "Valentine campaign",
                "brand_name": "Cake Shop",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Policy Enforcement Denied"
    assert body["reason"] == "approval_required"
    assert body["details"]["decision_id"]


@pytest.mark.asyncio
async def test_execute_skill_allows_publish_intent_with_approval_id():
    transport = ASGITransport(app=_make_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute",
            json={
                "agent_id": "AGT-MKT-HEALTH-001",
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
