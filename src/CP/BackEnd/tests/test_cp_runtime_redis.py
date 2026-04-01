from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
def test_cp_runtime_redis_health_proxies_payload(client, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")
    monkeypatch.setattr(
        "api.cp_runtime_redis.PlantGatewayClient.request_json",
        AsyncMock(
            return_value=type(
                "Resp",
                (),
                {"status_code": 200, "json": {"status": "ok", "db_index": 0}, "headers": {}},
            )()
        ),
    )

    response = client.get("/api/cp/runtime/redis/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.unit
def test_cp_runtime_redis_config_proxies_payload(client, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")
    monkeypatch.setattr(
        "api.cp_runtime_redis.PlantGatewayClient.request_json",
        AsyncMock(
            return_value=type(
                "Resp",
                (),
                {"status_code": 200, "json": {"service": "plant-backend", "db_index": 0}, "headers": {}},
            )()
        ),
    )

    response = client.get("/api/cp/runtime/redis/config")

    assert response.status_code == 200
    assert response.json()["service"] == "plant-backend"
