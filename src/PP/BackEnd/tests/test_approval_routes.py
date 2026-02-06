from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest


def _admin_token(settings, *, sub: str = "admin-1") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
async def test_approvals_requires_admin(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("PP_APPROVALS_STORE_PATH", str(store_path))

    from services import approvals as svc

    svc.default_approval_store.cache_clear()

    resp = await client.post(
        "/api/pp/approvals",
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-TRD-DELTA-001",
            "action": "place_order",
        },
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_approvals_mint_list_get(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("PP_APPROVALS_STORE_PATH", str(store_path))

    from services import approvals as svc

    svc.default_approval_store.cache_clear()

    from core.config import get_settings

    settings = get_settings()
    token = _admin_token(settings, sub="admin-99")

    minted = await client.post(
        "/api/pp/approvals",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-TRD-DELTA-001",
            "action": "place_order",
            "purpose": "trade_action",
            "correlation_id": "corr-1",
        },
    )

    assert minted.status_code == 200
    body = minted.json()
    assert body["approval_id"].startswith("APR-")
    assert body["requested_by"] == "admin-99"

    approval_id = body["approval_id"]

    listed = await client.get(
        "/api/pp/approvals?customer_id=CUST-1&limit=10",
        headers={"authorization": f"Bearer {token}"},
    )

    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body["count"] >= 1
    assert any(row.get("approval_id") == approval_id for row in listed_body.get("approvals", []))

    fetched = await client.get(
        f"/api/pp/approvals/{approval_id}",
        headers={"authorization": f"Bearer {token}"},
    )

    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["approval_id"] == approval_id
    assert fetched_body["action"] == "place_order"
