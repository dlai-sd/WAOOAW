from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from models.user import TokenData
from services import cp_refresh_revocations


@pytest.mark.unit
def test_default_store_uses_file_store(monkeypatch, tmp_path):
    """CP BackEnd must always use FileCPRefreshRevocationStore — no direct Redis."""
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("CP_REFRESH_REVOKE_STORE_PATH", str(tmp_path / "revocations.jsonl"))
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()

    store = cp_refresh_revocations.get_cp_refresh_revocation_store()

    assert isinstance(store, cp_refresh_revocations.FileCPRefreshRevocationStore)
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()


@pytest.mark.unit
def test_default_store_falls_back_to_file_without_redis(monkeypatch, tmp_path):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("CP_REFRESH_REVOKE_STORE_PATH", str(tmp_path / "revocations.jsonl"))
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()

    store = cp_refresh_revocations.get_cp_refresh_revocation_store()

    assert isinstance(store, cp_refresh_revocations.FileCPRefreshRevocationStore)
    cp_refresh_revocations.default_cp_refresh_revocation_store.cache_clear()
