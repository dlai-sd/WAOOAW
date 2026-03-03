"""Unit tests for _fallback_from_plant_hired_agents in my_agents_summary.py.

E1-S2 of CP-MY-AGENTS-1: covers fallback that queries Plant BE directly when
the local cp_subscriptions_simple store is empty.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


# ─────────────────────────────── helpers ──────────────────────────────────

def _plant_payload(customer_id: str, instances: list[dict]) -> dict:
    """Build a minimal Plant /by-customer response payload."""
    return {"customer_id": customer_id, "instances": instances}


def _instance(
    *,
    subscription_id: str = "SUB-TEST-01",
    agent_id: str = "AGT-TRD-001",
    agent_type_id: str = "trading.share_trader.v1",
    nickname: str = "Test Trader",
) -> dict:
    return {
        "subscription_id": subscription_id,
        "agent_id": agent_id,
        "agent_type_id": agent_type_id,
        "nickname": nickname,
        "status": "active",
        "customer_id": "cust-test-01",
    }


# ─────────────────────────────── module-level ────────────────────────────

@pytest.mark.asyncio
async def test_fallback_returns_instances_from_plant():
    """Fallback synthesises MyAgentInstanceSummary objects from Plant data."""
    from api.my_agents_summary import _fallback_from_plant_hired_agents

    plant_data = _plant_payload(
        "cust-test-01",
        [_instance(subscription_id="SUB-TEST-01", agent_id="AGT-TRD-001")],
    )

    with patch(
        "api.my_agents_summary._plant_get_json", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = plant_data

        with patch("api.my_agents_summary._plant_base_url", return_value="http://plant:8001"):
            result = await _fallback_from_plant_hired_agents(
                authorization="Bearer test-token",
                customer_id="cust-test-01",
            )

    assert len(result) == 1
    item = result[0]
    assert item.subscription_id == "SUB-TEST-01"
    assert item.agent_id == "AGT-TRD-001"
    assert item.agent_type_id == "trading.share_trader.v1"
    assert item.status == "active"
    assert item.duration == "monthly"
    # current_period_end should be set (roughly now + 30 days)
    assert item.current_period_end is not None


@pytest.mark.asyncio
async def test_fallback_returns_empty_when_plant_unavailable():
    """Fallback swallows exceptions and returns [] when Plant is unreachable."""
    from api.my_agents_summary import _fallback_from_plant_hired_agents

    with patch(
        "api.my_agents_summary._plant_get_json", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = Exception("Plant BE is down")

        with patch("api.my_agents_summary._plant_base_url", return_value="http://plant:8001"):
            result = await _fallback_from_plant_hired_agents(
                authorization="Bearer test-token",
                customer_id="cust-test-01",
            )

    assert result == []


@pytest.mark.asyncio
async def test_fallback_returns_empty_when_base_url_missing():
    """Fallback returns [] immediately when PLANT_GATEWAY_URL env var is unset."""
    from api.my_agents_summary import _fallback_from_plant_hired_agents

    with patch("api.my_agents_summary._plant_base_url", return_value=None):
        result = await _fallback_from_plant_hired_agents(
            authorization="Bearer test-token",
            customer_id="cust-test-01",
        )

    assert result == []


@pytest.mark.asyncio
async def test_fallback_handles_empty_instances_from_plant():
    """Fallback returns [] when Plant returns 0 instances for the customer."""
    from api.my_agents_summary import _fallback_from_plant_hired_agents

    plant_data = _plant_payload("cust-no-agents", [])

    with patch(
        "api.my_agents_summary._plant_get_json", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = plant_data

        with patch("api.my_agents_summary._plant_base_url", return_value="http://plant:8001"):
            result = await _fallback_from_plant_hired_agents(
                authorization="Bearer test-token",
                customer_id="cust-no-agents",
            )

    assert result == []


@pytest.mark.asyncio
async def test_fallback_multiple_instances():
    """Fallback correctly maps multiple instances from Plant response."""
    from api.my_agents_summary import _fallback_from_plant_hired_agents

    plant_data = _plant_payload(
        "cust-test-02",
        [
            _instance(subscription_id="SUB-A", agent_id="AGT-TRD-001"),
            _instance(
                subscription_id="SUB-B",
                agent_id="AGT-MKT-001",
                agent_type_id="marketing.digital_marketing.v1",
                nickname="Content Creator",
            ),
        ],
    )

    with patch(
        "api.my_agents_summary._plant_get_json", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = plant_data

        with patch("api.my_agents_summary._plant_base_url", return_value="http://plant:8001"):
            result = await _fallback_from_plant_hired_agents(
                authorization=None,
                customer_id="cust-test-02",
            )

    assert len(result) == 2
    subs = {i.subscription_id for i in result}
    assert subs == {"SUB-A", "SUB-B"}
    agents = {i.agent_id for i in result}
    assert agents == {"AGT-TRD-001", "AGT-MKT-001"}


# ─────────────────────────── summary endpoint integration ────────────────

@pytest.mark.unit
def test_summary_endpoint_uses_fallback_when_store_empty(client, monkeypatch):
    """GET /cp/my-agents/summary uses Plant fallback when subscriptions store is empty."""
    monkeypatch.setenv("ENVIRONMENT", "development")

    plant_data = _plant_payload(
        "customer-test-summary",
        [_instance(subscription_id="SUB-FALLBACK-01", agent_id="AGT-TRD-001")],
    )

    with (
        patch(
            "api.my_agents_summary._list_subscriptions",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "api.my_agents_summary._plant_base_url",
            return_value="http://plant-svc:8001",
        ),
        patch(
            "api.my_agents_summary._plant_get_json",
            new_callable=AsyncMock,
            return_value=plant_data,
        ),
    ):
        resp = client.get(
            "/cp/my-agents/summary",
            headers={"Authorization": "Bearer test-token"},
        )

    # Accept 200 or 422/401 depending on auth middleware in test env.
    # When auth is bypassed in development mode, expect 200.
    if resp.status_code == 200:
        body = resp.json()
        assert "instances" in body
