from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.api
def test_runtime_redis_health_returns_helper_payload(test_client, monkeypatch):
    monkeypatch.setattr(
        "api.v1.runtime_redis.redis_runtime.health_check",
        AsyncMock(
            return_value={
                "status": "ok",
                "redis": "ok",
                "service": "plant-backend",
                "db_index": 0,
                "namespaces": ["cache", "sessions"],
            }
        ),
    )

    response = test_client.get("/api/v1/runtime/redis/health")

    assert response.status_code == 200
    assert response.json()["db_index"] == 0


@pytest.mark.api
def test_runtime_redis_health_returns_503_on_failure(test_client, monkeypatch):
    monkeypatch.setattr(
        "api.v1.runtime_redis.redis_runtime.health_check",
        AsyncMock(side_effect=RuntimeError("down")),
    )

    response = test_client.get("/api/v1/runtime/redis/health")

    assert response.status_code == 503


@pytest.mark.api
def test_runtime_redis_config_returns_safe_metadata_only(test_client):
    response = test_client.get("/api/v1/runtime/redis/config")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "plant-backend"
    assert "db_index" in body
    assert "namespaces" in body
    assert "redis_url" not in body


@pytest.mark.api
def test_runtime_redis_invalidate_requires_admin(test_client):
    response = test_client.post(
        "/api/v1/runtime/redis/invalidate",
        json={"namespace": "cache", "key": "abc"},
    )

    assert response.status_code in {401, 403, 404}


@pytest.mark.api
def test_runtime_redis_invalidate_uses_runtime_service(test_client, monkeypatch):
    from main import app
    from api.v1.runtime_redis import _require_runtime_admin

    async def _allow_admin():
        return {"roles": ["admin"]}

    invalidate = AsyncMock(return_value={"namespace": "cache", "key": "abc", "deleted": 1})
    monkeypatch.setattr("api.v1.runtime_redis.redis_runtime.invalidate", invalidate)
    app.dependency_overrides[_require_runtime_admin] = _allow_admin

    try:
        response = test_client.post(
            "/api/v1/runtime/redis/invalidate",
            json={"namespace": "cache", "key": "abc"},
        )
    finally:
        app.dependency_overrides.pop(_require_runtime_admin, None)

    assert response.status_code == 200
    assert response.json()["deleted"] == 1
    invalidate.assert_awaited_once_with("cache", "abc")
