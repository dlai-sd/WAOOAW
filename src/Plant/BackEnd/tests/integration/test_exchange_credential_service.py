"""Integration tests for ExchangeCredentialService (TRADER-FULL-1 S1).

These tests run against a real asyncpg session in the docker-compose test environment.
In unit-test mode (no Postgres), they are skipped via the pytest mark.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import AsyncMock, MagicMock


# ── Unit-style tests (no DB required) ────────────────────────────────────────


class TestExchangeCredentialModelImport:
    """S1: Model imports without error."""

    def test_model_imports(self):
        from models.exchange_credential import ExchangeCredentialModel
        assert ExchangeCredentialModel.__tablename__ == "exchange_credentials"

    def test_service_imports(self):
        from services.exchange_credential_service import ExchangeCredentialService
        assert callable(ExchangeCredentialService)

    def test_mint_credential_ref_format(self):
        from services.exchange_credential_service import mint_credential_ref
        ref = mint_credential_ref()
        assert ref.startswith("EXCH-")
        assert len(ref) > 5


class TestFernetRoundTrip:
    """S1: Fernet encrypt/decrypt round-trip."""

    def test_encrypt_decrypt_round_trip(self):
        from services.exchange_credential_service import _encrypt, _decrypt
        plaintext = "my-api-key-xyz"
        encrypted = _encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = _decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypted_value_does_not_contain_plaintext(self):
        from services.exchange_credential_service import _encrypt
        plaintext = "SUPER_SECRET_API_KEY"
        encrypted = _encrypt(plaintext)
        assert plaintext not in encrypted


class TestExchangeCredentialServiceWithMockDb:
    """S1: Service methods behave correctly with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_upsert_returns_record(self):
        from services.exchange_credential_service import ExchangeCredentialService
        from models.exchange_credential import ExchangeCredentialModel

        fake_rec = MagicMock(spec=ExchangeCredentialModel)
        fake_rec.credential_ref = "EXCH-test001"
        fake_rec.customer_id = "CUST-1"
        fake_rec.validation_status = "pending"

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = fake_rec

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        svc = ExchangeCredentialService(mock_db)
        result = await svc.upsert(
            customer_id="CUST-1",
            exchange_provider="delta_exchange_india",
            api_key="ak_test",
            api_secret="as_test",
            default_coin="BTC",
            allowed_coins=["BTC"],
            risk_limits={},
        )

        assert result.credential_ref == "EXCH-test001"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_secrets_returns_decrypted(self):
        from services.exchange_credential_service import (
            ExchangeCredentialService,
            _encrypt,
        )
        from models.exchange_credential import ExchangeCredentialModel

        fake_rec = MagicMock(spec=ExchangeCredentialModel)
        fake_rec.encrypted_api_key = _encrypt("my-api-key")
        fake_rec.encrypted_api_secret = _encrypt("my-api-secret")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = fake_rec

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        svc = ExchangeCredentialService(mock_db)
        result = await svc.get_secrets(credential_ref="EXCH-test001")

        assert result is not None
        assert result["api_key"] == "my-api-key"
        assert result["api_secret"] == "my-api-secret"

    @pytest.mark.asyncio
    async def test_get_secrets_missing_returns_none(self):
        from services.exchange_credential_service import ExchangeCredentialService

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        svc = ExchangeCredentialService(mock_db)
        result = await svc.get_secrets(credential_ref="nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_validated_updates_status(self):
        from services.exchange_credential_service import ExchangeCredentialService
        from models.exchange_credential import ExchangeCredentialModel

        fake_rec = MagicMock(spec=ExchangeCredentialModel)
        fake_rec.validation_status = "pending"
        fake_rec.last_validated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = fake_rec

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        svc = ExchangeCredentialService(mock_db)
        await svc.mark_validated(credential_ref="EXCH-test001", status="valid")

        assert fake_rec.validation_status == "valid"
        assert fake_rec.last_validated_at is not None
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_validated_noop_for_missing_ref(self):
        from services.exchange_credential_service import ExchangeCredentialService

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        svc = ExchangeCredentialService(mock_db)
        # Should not raise
        await svc.mark_validated(credential_ref="nonexistent", status="valid")
        mock_db.commit.assert_not_awaited()
