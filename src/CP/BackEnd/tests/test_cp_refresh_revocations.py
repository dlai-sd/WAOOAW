from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from models.user import TokenData
from services import cp_refresh_revocations


@pytest.mark.unit
def test_default_store_uses_redis_when_configured(monkeypatch):
    fake_client = MagicMock()
    fake_client.get.return_value = None
    from_url = MagicMock(return_value=fake_client)

    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/3")
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()
    monkeypatch.setattr(cp_refresh_revocations.redis.Redis, "from_url", from_url)

    store = cp_refresh_revocations.get_cp_refresh_revocation_store()

    assert isinstance(store, cp_refresh_revocations.RedisCPRefreshRevocationStore)
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()


@pytest.mark.unit
def test_redis_store_revokes_and_checks_refresh_tokens(monkeypatch):
    fake_client = MagicMock()
    saved: dict[str, str] = {}

    def _set(key, value):
        saved[key] = value

    def _get(key):
        return saved.get(key)

    fake_client.set.side_effect = _set
    fake_client.get.side_effect = _get
    monkeypatch.setattr(cp_refresh_revocations.redis.Redis, "from_url", MagicMock(return_value=fake_client))

    store = cp_refresh_revocations.RedisCPRefreshRevocationStore("redis://redis:6379/3")
    revoked_at = datetime.now(timezone.utc)
    token = TokenData(
        user_id="user-1",
        email="user@example.com",
        token_type="refresh",
        iat=int((revoked_at - timedelta(seconds=5)).timestamp()),
        exp=int((revoked_at + timedelta(hours=1)).timestamp()),
    )

    store.revoke_user("user-1", revoked_at=revoked_at)

    assert store.is_refresh_token_revoked(token) is True


@pytest.mark.unit
def test_default_store_falls_back_to_file_without_redis(monkeypatch, tmp_path):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("CP_REFRESH_REVOKE_STORE_PATH", str(tmp_path / "revocations.jsonl"))
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()

    store = cp_refresh_revocations.get_cp_refresh_revocation_store()

    assert isinstance(store, cp_refresh_revocations.FileCPRefreshRevocationStore)
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()
