"""Tests for ops_cache Redis cache service (E5-E6).

Tests cover:
  - cache miss (no Redis configured) → returns None
  - cache miss (key absent in Redis) → returns None
  - cache hit → returns deserialized value without calling Plant
  - cache set stores value that can be retrieved via cache_get
  - graceful degradation when Redis raises on get
  - graceful degradation when Redis raises on set
  - _build_key produces different hashes for different params
  - _build_key produces the same hash for identical params (deterministic)
"""
from __future__ import annotations

import json
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_redis_mock(*, get_return=None, ping_ok=True):
    """Build a minimal async Redis mock."""
    mock = MagicMock()
    mock.ping = AsyncMock(return_value=True if ping_ok else (_ for _ in ()).throw(Exception("ping fail")))
    mock.get = AsyncMock(return_value=get_return)
    mock.set = AsyncMock(return_value=True)
    return mock


async def _reset_module_cache():
    """Reset the module-level _redis_client singleton between tests."""
    import services.ops_cache as oc

    oc._redis_client = None


# ---------------------------------------------------------------------------
# _build_key tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_build_key_deterministic():
    """Same inputs must always produce the same cache key."""
    await _reset_module_cache()
    from services.ops_cache import _build_key

    key1 = _build_key("subs", "/api/v1/subscriptions", {"customer_id": "C1"})
    key2 = _build_key("subs", "/api/v1/subscriptions", {"customer_id": "C1"})
    assert key1 == key2


@pytest.mark.unit
async def test_build_key_different_params_different_hash():
    """Different query params must produce different cache keys."""
    await _reset_module_cache()
    from services.ops_cache import _build_key

    key_a = _build_key("subs", "/api/v1/subscriptions", {"customer_id": "C1"})
    key_b = _build_key("subs", "/api/v1/subscriptions", {"customer_id": "C2"})
    assert key_a != key_b


@pytest.mark.unit
async def test_build_key_starts_with_pp_ops():
    """Cache keys must be scoped under pp:ops to avoid collisions."""
    await _reset_module_cache()
    from services.ops_cache import _build_key

    key = _build_key("subs", "/api/v1/subscriptions")
    assert key.startswith("pp:ops:subs:")


# ---------------------------------------------------------------------------
# cache_get tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_cache_get_returns_none_when_redis_not_configured():
    """If REDIS_URL is empty, cache_get returns None (no Redis call)."""
    await _reset_module_cache()
    import services.ops_cache as oc

    with patch.object(oc.settings, "REDIS_URL", ""):
        result = await oc.cache_get("subs", "/api/v1/subscriptions")
    assert result is None


@pytest.mark.unit
async def test_cache_get_returns_none_on_cache_miss():
    """cache_get returns None when key is absent in Redis."""
    await _reset_module_cache()
    import services.ops_cache as oc

    mock_redis = _make_redis_mock(get_return=None)
    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        result = await oc.cache_get("subs", "/api/v1/subscriptions", {"customer_id": "C1"})
    assert result is None


@pytest.mark.unit
async def test_cache_get_returns_deserialized_value_on_hit():
    """cache_get deserializes and returns the JSON-stored value on a cache hit."""
    await _reset_module_cache()
    import services.ops_cache as oc

    payload = [{"subscription_id": "sub-1", "status": "active"}]
    mock_redis = _make_redis_mock(get_return=json.dumps(payload))
    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        result = await oc.cache_get("subs", "/api/v1/subscriptions")
    assert result == payload


@pytest.mark.unit
async def test_cache_get_returns_none_on_redis_error():
    """cache_get swallows Redis errors and returns None (graceful degradation)."""
    await _reset_module_cache()
    import services.ops_cache as oc

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=Exception("connection refused"))
    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        result = await oc.cache_get("subs", "/api/v1/subscriptions")
    assert result is None


# ---------------------------------------------------------------------------
# cache_set tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_cache_set_stores_json_serialized_value():
    """cache_set calls redis.set with JSON-encoded value and expected TTL."""
    await _reset_module_cache()
    import services.ops_cache as oc

    mock_redis = _make_redis_mock()
    payload = {"subscription_id": "sub-1"}
    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch.object(oc.settings, "OPS_CACHE_TTL_SECONDS", 60),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        await oc.cache_set("sub", "/api/v1/subscriptions/sub-1", payload)

    mock_redis.set.assert_awaited_once()
    call_args = mock_redis.set.call_args
    # The second positional arg is the JSON-encoded value
    assert json.loads(call_args.args[1]) == payload
    assert call_args.kwargs.get("ex") == 60


@pytest.mark.unit
async def test_cache_set_is_noop_when_redis_not_configured():
    """cache_set silently does nothing when REDIS_URL is empty."""
    await _reset_module_cache()
    import services.ops_cache as oc

    with patch.object(oc.settings, "REDIS_URL", ""):
        # Should not raise
        await oc.cache_set("sub", "/api/v1/subscriptions/sub-1", {"id": "x"})


@pytest.mark.unit
async def test_cache_set_swallows_redis_errors():
    """cache_set swallows Redis errors silently (graceful degradation)."""
    await _reset_module_cache()
    import services.ops_cache as oc

    mock_redis = MagicMock()
    mock_redis.set = AsyncMock(side_effect=Exception("connection refused"))
    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        # Should not raise
        await oc.cache_set("sub", "/api/v1/subscriptions/sub-1", {"id": "x"})


# ---------------------------------------------------------------------------
# Round-trip test: set then get
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_cache_roundtrip_set_then_get():
    """Value stored with cache_set is returned by a subsequent cache_get."""
    await _reset_module_cache()
    import services.ops_cache as oc

    store: dict[str, str] = {}

    async def fake_set(key, value, ex=None):
        store[key] = value

    async def fake_get(key):
        return store.get(key)

    mock_redis = MagicMock()
    mock_redis.set = AsyncMock(side_effect=fake_set)
    mock_redis.get = AsyncMock(side_effect=fake_get)

    payload = [{"hired_instance_id": "inst-1"}]
    path = "/api/v1/hired-agents"
    params = {"customer_id": "C1"}

    with (
        patch.object(oc.settings, "REDIS_URL", "redis://localhost:6379"),
        patch.object(oc.settings, "OPS_CACHE_TTL_SECONDS", 60),
        patch("services.ops_cache._get_redis", AsyncMock(return_value=mock_redis)),
    ):
        await oc.cache_set("hired", path, payload, params)
        result = await oc.cache_get("hired", path, params)

    assert result == payload


@pytest.mark.unit
async def test_get_redis_connects_successfully_when_configured(monkeypatch):
    await _reset_module_cache()
    import services.ops_cache as oc

    mock_redis = _make_redis_mock()

    monkeypatch.setattr(oc.settings, "REDIS_URL", "redis://localhost:6379/2")
    monkeypatch.setitem(sys.modules, "redis.asyncio", types.SimpleNamespace(from_url=lambda *args, **kwargs: mock_redis))

    client = await oc._get_redis()

    assert client is mock_redis
    mock_redis.ping.assert_awaited_once()


@pytest.mark.unit
async def test_get_redis_returns_none_when_unavailable(monkeypatch):
    await _reset_module_cache()
    import services.ops_cache as oc

    monkeypatch.setattr(oc.settings, "REDIS_URL", "redis://localhost:6379/2")
    monkeypatch.setitem(
        sys.modules,
        "redis.asyncio",
        types.SimpleNamespace(
            from_url=lambda *args, **kwargs: MagicMock(
                ping=AsyncMock(side_effect=RuntimeError("down"))
            )
        ),
    )

    client = await oc._get_redis()

    assert client is None
