from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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


@pytest.mark.asyncio
async def test_approvals_list_filters_by_correlation_id(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("PP_APPROVALS_STORE_PATH", str(store_path))

    from services import approvals as svc

    svc.default_approval_store.cache_clear()

    from core.config import get_settings

    settings = get_settings()
    token = _admin_token(settings, sub="admin-99")

    created_one = await client.post(
        "/api/pp/approvals",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-TRD-DELTA-001",
            "action": "place_order",
            "correlation_id": "corr-123",
        },
    )
    assert created_one.status_code == 200

    created_two = await client.post(
        "/api/pp/approvals",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-TRD-DELTA-001",
            "action": "place_order",
            "correlation_id": "corr-999",
        },
    )
    assert created_two.status_code == 200

    listed = await client.get(
        "/api/pp/approvals?correlation_id=corr-123&limit=50",
        headers={"authorization": f"Bearer {token}"},
    )

    assert listed.status_code == 200
    body = listed.json()
    assert body["count"] == 1
    assert body["approvals"][0]["correlation_id"] == "corr-123"


def _make_plant(status_code: int, body):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    response.text = str(body)
    return response


@pytest.mark.asyncio
async def test_approvals_review_queue_returns_enriched_context(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("PP_APPROVALS_STORE_PATH", str(store_path))

    from services import approvals as svc
    from clients.plant_client import get_plant_client
    from core.config import get_settings

    svc.default_approval_store.cache_clear()
    settings = get_settings()
    token = _admin_token(settings, sub="admin-99")

    created = await client.post(
        "/api/pp/approvals",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-MKT-HEALTH-001",
            "action": "publish",
            "purpose": "review_queue",
        },
    )
    assert created.status_code == 200

    plant = SimpleNamespace(
        _request=AsyncMock(
            side_effect=[
                _make_plant(
                    200,
                    {
                        "customer_id": "CUST-1",
                        "instances": [
                            {
                                "hired_instance_id": "HAI-123",
                                "agent_id": "AGT-MKT-HEALTH-001",
                                "nickname": "Healthcare Content Agent",
                            }
                        ],
                    },
                ),
                _make_plant(
                    200,
                    [
                        {
                            "batch_id": "BATCH-1",
                            "agent_id": "AGT-MKT-HEALTH-001",
                            "customer_id": "CUST-1",
                            "brand_name": "WAOOAW Care",
                            "theme": "Patient follow-up reminders",
                            "status": "pending_review",
                            "posts": [
                                {
                                    "post_id": "POST-1",
                                    "channel": "linkedin",
                                    "text": "Draft follow-up reminder post for patients.",
                                    "review_status": "pending_review",
                                    "execution_status": "not_scheduled",
                                }
                            ],
                        }
                    ],
                ),
            ]
        )
    )
    app.dependency_overrides[get_plant_client] = lambda: plant

    try:
        resp = await client.get(
            "/api/pp/approvals/review-queue?customer_id=CUST-1",
            headers={"authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    approval = body["approvals"][0]
    assert approval["customer_label"] == "CUST-1"
    assert approval["agent_label"] == "Healthcare Content Agent"
    assert approval["hired_instance_id"] == "HAI-123"
    assert approval["review_state"] == "pending_review"
    assert approval["deliverable_preview"]["batch_id"] == "BATCH-1"
    assert approval["deliverable_preview"]["post_id"] == "POST-1"
    assert approval["deliverable_preview"]["brand_name"] == "WAOOAW Care"


@pytest.mark.asyncio
async def test_approvals_review_queue_surfaces_upstream_failure(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("PP_APPROVALS_STORE_PATH", str(store_path))

    from services import approvals as svc
    from clients.plant_client import get_plant_client
    from core.config import get_settings

    svc.default_approval_store.cache_clear()
    settings = get_settings()
    token = _admin_token(settings, sub="admin-99")

    created = await client.post(
        "/api/pp/approvals",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "agent_id": "AGT-MKT-HEALTH-001",
            "action": "publish",
        },
    )
    assert created.status_code == 200

    plant = SimpleNamespace(_request=AsyncMock(return_value=_make_plant(502, {"detail": "plant unavailable"})))
    app.dependency_overrides[get_plant_client] = lambda: plant

    try:
        resp = await client.get(
            "/api/pp/approvals/review-queue?customer_id=CUST-1",
            headers={"authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
