from __future__ import annotations

from unittest.mock import Mock

from services import security_throttle


def test_default_throttle_store_uses_cached_fail_fast_redis_client(monkeypatch):
    fake_client = Mock()

    monkeypatch.setattr(security_throttle.default_throttle_store, "cache_clear", security_throttle.default_throttle_store.cache_clear)
    monkeypatch.setattr(security_throttle.get_security_throttle, "cache_clear", security_throttle.get_security_throttle.cache_clear)
    security_throttle.default_throttle_store.cache_clear()
    security_throttle.get_security_throttle.cache_clear()

    get_redis = Mock(return_value=fake_client)
    monkeypatch.setattr(security_throttle, "get_redis", get_redis)
    monkeypatch.setattr(security_throttle.settings, "redis_url", "redis://10.0.0.3:6379/0")

    store_first = security_throttle.default_throttle_store()
    store_second = security_throttle.default_throttle_store()

    assert isinstance(store_first, security_throttle.RedisThrottleStore)
    assert store_first is store_second
    assert store_first._client is fake_client
    get_redis.assert_called_once_with()


def test_get_security_throttle_is_cached(monkeypatch):
    security_throttle.default_throttle_store.cache_clear()
    security_throttle.get_security_throttle.cache_clear()

    fake_store = security_throttle.InMemoryThrottleStore()
    default_store = Mock(return_value=fake_store)
    monkeypatch.setattr(security_throttle, "default_throttle_store", default_store)

    throttle_first = security_throttle.get_security_throttle()
    throttle_second = security_throttle.get_security_throttle()

    assert throttle_first is throttle_second
    default_store.assert_called_once_with()