from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services import redis_runtime


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_returns_ok(monkeypatch):
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    monkeypatch.setattr(redis_runtime, "_redis_client", client)

    result = await redis_runtime.health_check()

    assert result["redis"] == "ok"
    assert result["service"] == "plant-backend"
    assert result["db_index"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_raises_on_ping_failure(monkeypatch):
    client = MagicMock()
    client.ping = AsyncMock(side_effect=RuntimeError("redis down"))
    monkeypatch.setattr(redis_runtime, "_redis_client", client)

    with pytest.raises(RuntimeError, match="redis down"):
        await redis_runtime.health_check()


@pytest.mark.unit
def test_effective_db_index_parses_from_runtime_url():
    assert redis_runtime.effective_db_index("redis://host:6379/0") == 0
    assert redis_runtime.effective_db_index("redis://host:6379/7") == 7
    assert redis_runtime.effective_db_index("redis://host:6379") == 0
