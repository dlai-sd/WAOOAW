from __future__ import annotations

from typing import Any, Dict, Optional

import pytest


class _FakePlantClient:
    def __init__(self) -> None:
        self.calls = []

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
    ):
        self.calls.append({"method": method, "path": path, "headers": headers or {}, "json": json_body, "params": params or {}})
        return type(
            "R",
            (),
            {
                "status_code": 200,
                "json": {
                    "agent_id": (path.split("/")[-2] if "/reference-agents/" in path else "AGT-TRD-DELTA-001"),
                    "agent_type": "trading",
                    "status": "draft",
                    "draft": dict(json_body or {}),
                },
                "headers": {},
            },
        )()


@pytest.mark.usefixtures("auth_headers")
def test_trading_draft_and_approve_execute(client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setenv("CP_APPROVALS_STORE_PATH", str(tmp_path / "cp_approvals.jsonl"))
    from services import cp_approvals as approvals

    approvals.default_cp_approval_store.cache_clear()

    from main import app
    from api.trading import get_plant_gateway_client

    fake = _FakePlantClient()
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    draft = client.post(
        "/api/cp/trading/draft-plan",
        headers=auth_headers,
        json={
            "agent_id": "AGT-TRD-DELTA-001",
            "exchange_account_id": "EXCH-1",
            "coin": "BTC",
            "units": 1,
            "side": "long",
            "action": "enter",
            "market": True,
        },
    )
    assert draft.status_code == 200
    body = draft.json()
    assert body["agent_type"] == "trading"
    assert body["draft"]["customer_id"].startswith("CUST-")

    executed = client.post(
        "/api/cp/trading/approve-execute",
        headers=auth_headers,
        json={
            "agent_id": "AGT-TRD-DELTA-001",
            "intent_action": "place_order",
            "exchange_account_id": "EXCH-1",
            "coin": "BTC",
            "units": 1,
            "side": "long",
            "action": "enter",
            "market": True,
        },
    )
    assert executed.status_code == 200
    body2 = executed.json()
    assert body2["draft"]["intent_action"] == "place_order"
    assert body2["draft"]["approval_id"].startswith("APR-")

    # Ensure we called Plant run endpoint.
    assert any("api/v1/reference-agents/AGT-TRD-DELTA-001/run" in c["path"] for c in fake.calls)

    app.dependency_overrides.clear()
