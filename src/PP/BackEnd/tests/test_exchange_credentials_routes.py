from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
import pytest


def _admin_token(settings, *, sub: str = "admin-1") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
async def test_exchange_credentials_requires_admin(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "exchange_credentials.jsonl"
    monkeypatch.setenv("PP_EXCHANGE_CREDENTIALS_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_EXCHANGE_CREDENTIALS_SECRET", "test-secret")

    from services import exchange_credentials as svc

    svc.default_exchange_credential_store.cache_clear()
    svc._fernet.cache_clear()

    resp = await client.put(
        "/api/pp/exchange-credentials",
        json={
            "customer_id": "CUST-1",
            "exchange_provider": "delta_exchange_india",
            "api_key": "k",
            "api_secret": "s",
        },
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_exchange_credentials_upsert_and_get_bundle(client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "exchange_credentials.jsonl"
    monkeypatch.setenv("PP_EXCHANGE_CREDENTIALS_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_EXCHANGE_CREDENTIALS_SECRET", "test-secret")

    from services import exchange_credentials as svc

    svc.default_exchange_credential_store.cache_clear()
    svc._fernet.cache_clear()

    from core.config import get_settings

    settings = get_settings()
    token = _admin_token(settings)

    upsert = await client.put(
        "/api/pp/exchange-credentials",
        headers={"authorization": f"Bearer {token}"},
        json={
            "customer_id": "CUST-1",
            "exchange_provider": "delta_exchange_india",
            "api_key": "test-key",
            "api_secret": "test-secret",
        },
    )

    assert upsert.status_code == 200
    exchange_account_id = upsert.json()["exchange_account_id"]

    bundle = await client.get(
        f"/api/pp/exchange-credentials/{exchange_account_id}",
        headers={"authorization": f"Bearer {token}"},
    )

    assert bundle.status_code == 200
    body = bundle.json()
    assert body["exchange_account_id"] == exchange_account_id
    assert body["api_key"] == "test-key"
    assert body["api_secret"] == "test-secret"
