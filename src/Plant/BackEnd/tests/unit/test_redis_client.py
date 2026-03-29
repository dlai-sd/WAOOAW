from __future__ import annotations

from unittest.mock import Mock

from core import redis_client


def test_get_redis_uses_fail_fast_timeouts(monkeypatch):
    fake_client = Mock()
    from_url = Mock(return_value=fake_client)

    monkeypatch.setattr(redis_client.redis.Redis, "from_url", from_url)
    monkeypatch.setattr(redis_client, "_sync_client", None)

    client = redis_client.get_redis()

    assert client is fake_client
    from_url.assert_called_once_with(
        redis_client.settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=redis_client.REDIS_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=redis_client.REDIS_SOCKET_TIMEOUT_SECONDS,
    )


def test_get_async_redis_uses_fail_fast_timeouts(monkeypatch):
    fake_client = Mock()
    from_url = Mock(return_value=fake_client)

    monkeypatch.setattr(redis_client.aioredis.Redis, "from_url", from_url)
    monkeypatch.setattr(redis_client, "_async_client", None)

    client = redis_client.get_async_redis()

    assert client is fake_client
    from_url.assert_called_once_with(
        redis_client.settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=redis_client.REDIS_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=redis_client.REDIS_SOCKET_TIMEOUT_SECONDS,
    )