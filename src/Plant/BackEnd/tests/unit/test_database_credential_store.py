"""Tests for DatabaseCredentialStore and DatabaseCredentialResolver."""

import pytest
from unittest.mock import AsyncMock, patch

from services.database_credential_store import DatabaseCredentialStore, CredentialRecord, mint_credential_ref
from services.social_credential_resolver import DatabaseCredentialResolver, CredentialResolutionError, StoredSocialCredentials


class TestMintCredentialRef:
    def test_format(self):
        ref = mint_credential_ref()
        assert ref.startswith("CRED-")
        assert len(ref) > 10

    def test_unique(self):
        refs = {mint_credential_ref() for _ in range(50)}
        assert len(refs) == 50


class TestDatabaseCredentialResolver:
    """Test the DB-backed resolver that replaces CP HTTP round-trips."""

    @pytest.mark.asyncio
    async def test_resolve_returns_credentials_from_db_and_secret_manager(self):
        """Resolve should look up credential_ref in DB, then read secrets from Secret Manager."""
        mock_db = AsyncMock()

        # Mock the DB credential store to return a record
        fake_record = CredentialRecord(
            credential_ref="CRED-abc123",
            customer_id="CUST-001",
            platform="youtube",
            posting_identity="My Channel",
            secret_manager_ref="local://secrets/test-secret/versions/latest",
        )

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore, patch(
            "services.secret_manager_adapter.get_secret_manager_adapter"
        ) as mock_adapter_factory:
            mock_store = MockStore.return_value
            mock_store.get_by_credential_ref = AsyncMock(return_value=fake_record)

            mock_adapter = AsyncMock()
            mock_adapter.read_secret = AsyncMock(
                return_value={
                    "access_token": "ya29.live-token",
                    "refresh_token": "1//refresh-token",
                }
            )
            mock_adapter_factory.return_value = mock_adapter

            resolver = DatabaseCredentialResolver(mock_db)
            result = await resolver.resolve(
                customer_id="CUST-001", credential_ref="CRED-abc123"
            )

            assert result.access_token == "ya29.live-token"
            assert result.refresh_token == "1//refresh-token"
            assert result.credential_ref == "CRED-abc123"
            assert result.customer_id == "CUST-001"
            assert result.platform == "youtube"

    @pytest.mark.asyncio
    async def test_resolve_raises_when_not_found_in_db(self):
        mock_db = AsyncMock()

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore:
            mock_store = MockStore.return_value
            mock_store.get_by_credential_ref = AsyncMock(return_value=None)

            resolver = DatabaseCredentialResolver(mock_db)
            with pytest.raises(CredentialResolutionError, match="not found in Plant DB"):
                await resolver.resolve(
                    customer_id="CUST-001", credential_ref="CRED-missing"
                )

    @pytest.mark.asyncio
    async def test_resolve_raises_when_no_secret_manager_ref(self):
        mock_db = AsyncMock()
        fake_record = CredentialRecord(
            credential_ref="CRED-abc123",
            customer_id="CUST-001",
            platform="youtube",
            secret_manager_ref=None,
        )

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore:
            mock_store = MockStore.return_value
            mock_store.get_by_credential_ref = AsyncMock(return_value=fake_record)

            resolver = DatabaseCredentialResolver(mock_db)
            with pytest.raises(CredentialResolutionError, match="No secret_manager_ref"):
                await resolver.resolve(
                    customer_id="CUST-001", credential_ref="CRED-abc123"
                )

    @pytest.mark.asyncio
    async def test_resolve_raises_when_secret_manager_empty(self):
        mock_db = AsyncMock()
        fake_record = CredentialRecord(
            credential_ref="CRED-abc123",
            customer_id="CUST-001",
            platform="youtube",
            secret_manager_ref="local://secrets/test-secret/versions/latest",
        )

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore, patch(
            "services.secret_manager_adapter.get_secret_manager_adapter"
        ) as mock_adapter_factory:
            mock_store = MockStore.return_value
            mock_store.get_by_credential_ref = AsyncMock(return_value=fake_record)
            mock_adapter = AsyncMock()
            mock_adapter.read_secret = AsyncMock(return_value={})
            mock_adapter_factory.return_value = mock_adapter

            resolver = DatabaseCredentialResolver(mock_db)
            with pytest.raises(CredentialResolutionError, match="empty payload"):
                await resolver.resolve(
                    customer_id="CUST-001", credential_ref="CRED-abc123"
                )

    @pytest.mark.asyncio
    async def test_upsert_stores_credential_in_db_and_secret_manager(self):
        """Upsert should write secrets to Secret Manager and the record to DB."""
        mock_db = AsyncMock()

        fake_record = CredentialRecord(
            credential_ref="CRED-new123",
            customer_id="CUST-001",
            platform="youtube",
            posting_identity="My Channel",
            secret_manager_ref="local://secrets/test/versions/latest",
        )

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore, patch(
            "services.secret_manager_adapter.get_secret_manager_adapter"
        ) as mock_adapter_factory:
            mock_store = MockStore.return_value
            mock_store.upsert = AsyncMock(return_value=fake_record)

            mock_adapter = AsyncMock()
            mock_adapter.write_secret = AsyncMock(
                return_value="local://secrets/test/versions/latest"
            )
            mock_adapter_factory.return_value = mock_adapter

            resolver = DatabaseCredentialResolver(mock_db)
            result = await resolver.upsert(
                customer_id="CUST-001",
                platform="youtube",
                posting_identity="My Channel",
                access_token="ya29.token",
                refresh_token="1//refresh",
            )

            assert isinstance(result, StoredSocialCredentials)
            assert result.credential_ref == "CRED-new123"
            mock_adapter.write_secret.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_access_token(self):
        mock_db = AsyncMock()
        fake_record = CredentialRecord(
            credential_ref="CRED-upd",
            customer_id="CUST-001",
            platform="youtube",
            secret_manager_ref="local://secrets/test/versions/latest",
        )

        with patch(
            "services.database_credential_store.DatabaseCredentialStore"
        ) as MockStore, patch(
            "services.secret_manager_adapter.get_secret_manager_adapter"
        ) as mock_adapter_factory:
            mock_store = MockStore.return_value
            mock_store.get_by_credential_ref = AsyncMock(return_value=fake_record)
            mock_store.update_secret_manager_ref = AsyncMock(return_value=True)

            mock_adapter = AsyncMock()
            mock_adapter.read_secret = AsyncMock(
                return_value={"access_token": "old-token", "refresh_token": "rt"}
            )
            mock_adapter.update_secret = AsyncMock(
                return_value="local://secrets/test/versions/latest"
            )
            mock_adapter_factory.return_value = mock_adapter

            resolver = DatabaseCredentialResolver(mock_db)
            await resolver.update_access_token(
                customer_id="CUST-001",
                credential_ref="CRED-upd",
                new_access_token="ya29.new-token",
            )

            mock_adapter.update_secret.assert_called_once()
            call_payload = mock_adapter.update_secret.call_args[0][1]
            assert call_payload["access_token"] == "ya29.new-token"


class TestLocalSecretManagerAdapter:
    """Test the in-memory adapter used for dev/CI."""

    @pytest.mark.asyncio
    async def test_write_and_read_roundtrip(self):
        from services.secret_manager_adapter import LocalSecretManagerAdapter

        adapter = LocalSecretManagerAdapter()
        ref = await adapter.write_secret("test-id", {"access_token": "tk1"})
        assert ref.startswith("local://secrets/")

        result = await adapter.read_secret(ref)
        assert result["access_token"] == "tk1"

    @pytest.mark.asyncio
    async def test_update_overwrites(self):
        from services.secret_manager_adapter import LocalSecretManagerAdapter

        adapter = LocalSecretManagerAdapter()
        ref = await adapter.write_secret("update-test", {"access_token": "old"})
        updated_ref = await adapter.update_secret(ref, {"access_token": "new"})
        assert updated_ref == ref

        result = await adapter.read_secret(ref)
        assert result["access_token"] == "new"

    @pytest.mark.asyncio
    async def test_read_missing_returns_empty(self):
        from services.secret_manager_adapter import LocalSecretManagerAdapter

        adapter = LocalSecretManagerAdapter()
        result = await adapter.read_secret("local://secrets/nonexistent/versions/latest")
        assert result == {}
