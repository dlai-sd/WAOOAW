from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.unit
def test_health_ready_uses_runtime_service(test_client, monkeypatch):
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock())
    session.close = AsyncMock(return_value=None)
    connector = SimpleNamespace(get_session=AsyncMock(return_value=session))

    monkeypatch.setattr("core.database._connector", connector)
    monkeypatch.setattr(
        "services.redis_runtime.health_check",
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

    response = test_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["redis"] == "ok"
