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
        if method == "GET" and path.endswith("/marketing/draft-batches"):
            return type(
                "R",
                (),
                {
                    "status_code": 200,
                    "json": [
                        {
                            "batch_id": "b1",
                            "agent_id": "AGT-1",
                            "customer_id": (params or {}).get("customer_id"),
                            "theme": "theme",
                            "brand_name": "brand",
                            "created_at": "2026-01-01T00:00:00Z",
                            "status": "pending_review",
                            "posts": [
                                {
                                    "post_id": "p-pending",
                                    "channel": "instagram",
                                    "text": "pending",
                                    "review_status": "pending_review",
                                },
                                {
                                    "post_id": "p-approved",
                                    "channel": "instagram",
                                    "text": "hi",
                                    "review_status": "approved",
                                    "approval_id": "APR-existing",
                                }
                            ],
                        }
                    ],
                    "headers": {},
                },
            )()
        if method == "POST" and "/draft-posts/" in path and path.endswith("/approve"):
            return type(
                "R",
                (),
                {"status_code": 200, "json": {"post_id": path.split("/")[-2], "review_status": "approved", "approval_id": (json_body or {}).get("approval_id")}, "headers": {}},
            )()
        if method == "POST" and "/draft-posts/" in path and path.endswith("/schedule"):
            return type(
                "R",
                (),
                {
                    "status_code": 200,
                    "json": {
                        "post_id": path.split("/")[-2],
                        "execution_status": "scheduled",
                        "scheduled_at": (json_body or {}).get("scheduled_at"),
                    },
                    "headers": {},
                },
            )()
        return type("R", (), {"status_code": 500, "json": {"error": "unexpected"}, "headers": {}})()


@pytest.mark.usefixtures("auth_headers")
def test_marketing_review_list_and_approve(client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setenv("CP_APPROVALS_STORE_PATH", str(tmp_path / "cp_approvals.jsonl"))
    from services import cp_approvals as approvals

    approvals.default_cp_approval_store.cache_clear()

    from main import app
    from api.marketing_review import get_plant_gateway_client

    fake = _FakePlantClient()
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    listed = client.get("/api/cp/marketing/draft-batches", headers=auth_headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)

    rejected = client.post(
        "/api/cp/marketing/draft-posts/reject",
        headers=auth_headers,
        json={"post_id": "p-pending", "reason": "no thanks"},
    )
    assert rejected.status_code == 200

    listed_after = client.get("/api/cp/marketing/draft-batches", headers=auth_headers)
    assert listed_after.status_code == 200
    rows = listed_after.json()
    assert isinstance(rows, list)
    assert rows
    post_ids = [p.get("post_id") for p in (rows[0].get("posts") or [])]
    assert "p-pending" not in post_ids

    approved = client.post(
        "/api/cp/marketing/draft-posts/approve",
        headers=auth_headers,
        json={"post_id": "p1"},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["post_id"] == "p1"
    assert body["review_status"] == "approved"
    assert body["approval_id"].startswith("APR-")

    app.dependency_overrides.clear()


@pytest.mark.usefixtures("auth_headers")
def test_marketing_review_schedule(client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setenv("CP_APPROVALS_STORE_PATH", str(tmp_path / "cp_approvals.jsonl"))
    from services import cp_approvals as approvals

    approvals.default_cp_approval_store.cache_clear()

    from main import app
    from api.marketing_review import get_plant_gateway_client

    fake = _FakePlantClient()
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    scheduled = client.post(
        "/api/cp/marketing/draft-posts/schedule",
        headers=auth_headers,
        json={"post_id": "p-approved", "scheduled_at": "2026-02-07T10:30:00+05:30"},
    )
    assert scheduled.status_code == 200
    body = scheduled.json()
    assert body["post_id"] == "p-approved"
    assert body["execution_status"] == "scheduled"

    app.dependency_overrides.clear()
