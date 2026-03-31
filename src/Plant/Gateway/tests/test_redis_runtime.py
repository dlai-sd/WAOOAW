from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import redis_runtime


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_uses_fast_fail_timeouts(monkeypatch):
    fake_client = MagicMock()
    from_url = MagicMock(return_value=fake_client)

    monkeypatch.setattr(redis_runtime, "_redis_client", None)
    monkeypatch.setattr(redis_runtime.aioredis.Redis, "from_url", from_url)

    client = await redis_runtime.get_client()

    assert client is fake_client
    from_url.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enqueue_budget_update_schedules_background_work(monkeypatch):
    apply_update = AsyncMock(return_value=None)
    created_tasks: list[object] = []

    def fake_create_task(coro):
        created_tasks.append(coro)

        class _Task:
            pass

        return _Task()

    monkeypatch.setattr(redis_runtime, "_apply_budget_update", apply_update)
    monkeypatch.setattr(redis_runtime.asyncio, "create_task", fake_create_task)

    await redis_runtime.enqueue_budget_update("agent-1", "customer-1", Decimal("0.5"))

    assert len(created_tasks) == 1
    await created_tasks[0]
    apply_update.assert_awaited_once_with("agent-1", "customer-1", Decimal("0.5"))


@pytest.mark.unit
def test_effective_db_index_parses_from_url():
    assert redis_runtime.effective_db_index("redis://host:6379/1") == 1
