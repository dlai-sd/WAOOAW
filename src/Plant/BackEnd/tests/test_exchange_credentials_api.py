"""Unit tests for Exchange Credentials API (TRADER-FULL-1 S2 + S4)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi import FastAPI


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_fake_rec(
    credential_ref="EXCH-abc123",
    customer_id="CUST-1",
    exchange_provider="delta_exchange_india",
    default_coin="BTC",
    allowed_coins=None,
    risk_limits=None,
    validation_status="pending",
):
    rec = MagicMock()
    rec.credential_ref = credential_ref
    rec.customer_id = customer_id
    rec.exchange_provider = exchange_provider
    rec.default_coin = default_coin
    rec.allowed_coins = allowed_coins or ["BTC"]
    rec.risk_limits = risk_limits or {}
    rec.validation_status = validation_status
    return rec


def _build_app():
    from api.v1.exchange_credentials import router
    from core.database import get_db_session, get_read_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    class _FakeDb:
        def add(self, obj):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

        async def execute(self, stmt):
            return MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))

        async def close(self):
            pass

    async def _fake_db():
        yield _FakeDb()

    app.dependency_overrides[get_db_session] = _fake_db
    app.dependency_overrides[get_read_db_session] = _fake_db
    return app


@pytest.fixture
async def client():
    app = _build_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


# ── S2 tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_returns_public_view_no_secrets(client, monkeypatch):
    """POST returns 201 with credential_ref; no api_key/api_secret in response."""
    fake_rec = _make_fake_rec()

    async def _fake_upsert(self, **kwargs):
        return fake_rec

    monkeypatch.setattr(
        "api.v1.exchange_credentials.ExchangeCredentialService.upsert",
        _fake_upsert,
    )

    resp = await client.post(
        "/api/v1/hired-agents/trader-001/exchange-credentials",
        json={
            "customer_id": "CUST-1",
            "exchange_provider": "delta_exchange_india",
            "api_key": "ak_test",
            "api_secret": "as_test",
            "default_coin": "BTC",
            "allowed_coins": ["BTC"],
            "risk_limits": {},
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["credential_ref"] == "EXCH-abc123"
    assert body["customer_id"] == "CUST-1"
    assert "api_key" not in body
    assert "api_secret" not in body
    assert "encrypted_api_key" not in body
    assert "encrypted_api_secret" not in body


@pytest.mark.asyncio
async def test_dual_write_called_in_dual_write_mode(monkeypatch):
    """Firestore set_document is called when DATA_ROUTER_MODE=dual_write."""
    monkeypatch.setenv("DATA_ROUTER_MODE", "dual_write")
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    fake_rec = _make_fake_rec()

    async def _fake_upsert(self, **kwargs):
        return fake_rec

    with patch(
        "api.v1.exchange_credentials.ExchangeCredentialService.upsert",
        new=_fake_upsert,
    ):
        with patch(
            "api.v1.exchange_credentials.set_document",
            new=AsyncMock(return_value=True),
        ) as mock_set:
            app = _build_app()
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
                await http_client.post(
                    "/api/v1/hired-agents/trader-001/exchange-credentials",
                    json={
                        "customer_id": "CUST-1",
                        "exchange_provider": "delta_exchange_india",
                        "api_key": "ak",
                        "api_secret": "as",
                        "default_coin": "BTC",
                        "allowed_coins": ["BTC"],
                        "risk_limits": {},
                    },
                )
            # Task was created — allow event loop to flush
            import asyncio
            await asyncio.sleep(0)

    monkeypatch.setenv("DATA_ROUTER_MODE", "sql")
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()


@pytest.mark.asyncio
async def test_dual_write_not_called_in_sql_mode(monkeypatch):
    """Firestore set_document is NOT called when DATA_ROUTER_MODE=sql."""
    monkeypatch.setenv("DATA_ROUTER_MODE", "sql")
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    fake_rec = _make_fake_rec()

    async def _fake_upsert(self, **kwargs):
        return fake_rec

    with patch(
        "api.v1.exchange_credentials.ExchangeCredentialService.upsert",
        new=_fake_upsert,
    ):
        with patch(
            "api.v1.exchange_credentials.set_document",
            new=AsyncMock(return_value=True),
        ) as mock_set:
            app = _build_app()
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
                await http_client.post(
                    "/api/v1/hired-agents/trader-001/exchange-credentials",
                    json={
                        "customer_id": "CUST-1",
                        "exchange_provider": "delta_exchange_india",
                        "api_key": "ak",
                        "api_secret": "as",
                        "default_coin": "BTC",
                        "allowed_coins": ["BTC"],
                        "risk_limits": {},
                    },
                )
            import asyncio
            await asyncio.sleep(0)
            mock_set.assert_not_called()


# ── S4 tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_returns_valid_in_test_env(monkeypatch):
    """POST /.../validate returns readable=true in test environment (mock path)."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    async def _fake_get_secrets(self, *, credential_ref):
        return {"api_key": "ak_test", "api_secret": "as_test"}

    async def _fake_mark_validated(self, *, credential_ref, status):
        pass

    with patch(
        "api.v1.exchange_credentials.ExchangeCredentialService.get_secrets",
        new=_fake_get_secrets,
    ):
        with patch(
            "api.v1.exchange_credentials.ExchangeCredentialService.mark_validated",
            new=_fake_mark_validated,
        ):
            app = _build_app()
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
                resp = await http_client.post(
                    "/api/v1/hired-agents/trader-001/exchange-credentials/EXCH-abc/validate"
                )

    assert resp.status_code == 200
    body = resp.json()
    assert body["readable"] is True
    assert body["tradeable"] is True
    assert body["validation_status"] == "valid"


@pytest.mark.asyncio
async def test_validate_404_for_missing_ref(monkeypatch):
    """POST /.../validate with non-existent credential_ref returns 404."""
    async def _fake_get_secrets_none(self, *, credential_ref):
        return None

    with patch(
        "api.v1.exchange_credentials.ExchangeCredentialService.get_secrets",
        new=_fake_get_secrets_none,
    ):
        app = _build_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
            resp = await http_client.post(
                "/api/v1/hired-agents/trader-001/exchange-credentials/MISSING/validate"
            )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_key_not_in_logs(monkeypatch, caplog):
    """api_key value must never appear in any log output."""
    import logging

    monkeypatch.setenv("ENVIRONMENT", "test")
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    secret_api_key = "SUPER_SECRET_KEY_XYZ"

    async def _fake_get_secrets(self, *, credential_ref):
        return {"api_key": secret_api_key, "api_secret": "as_test"}

    async def _fake_mark_validated(self, *, credential_ref, status):
        pass

    with caplog.at_level(logging.DEBUG):
        with patch(
            "api.v1.exchange_credentials.ExchangeCredentialService.get_secrets",
            new=_fake_get_secrets,
        ):
            with patch(
                "api.v1.exchange_credentials.ExchangeCredentialService.mark_validated",
                new=_fake_mark_validated,
            ):
                app = _build_app()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
                    await http_client.post(
                        "/api/v1/hired-agents/trader-001/exchange-credentials/EXCH-abc/validate"
                    )

    assert secret_api_key not in caplog.text
