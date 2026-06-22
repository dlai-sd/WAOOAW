"""Unit tests for FirestoreClient (INFRA-ROUTING-1 S2)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _reset_firestore_client():
    """Reset the module-level _fs_client and _breaker singletons between tests."""
    import core.firestore_client as fc_module
    fc_module._fs_client = None
    # Reset circuit breaker state
    fc_module._breaker._failures = 0
    fc_module._breaker._opened_at = None


class TestFirestoreClientImport:
    def test_imports_succeed(self):
        from core.firestore_client import get_document, set_document
        assert callable(get_document)
        assert callable(set_document)

    def test_pii_masking_filter_attached(self):
        import logging
        from core.logging import PiiMaskingFilter
        import core.firestore_client as fc_module
        fc_logger = logging.getLogger(fc_module.__name__)
        assert any(isinstance(f, PiiMaskingFilter) for f in fc_logger.filters)


class TestFirestoreClientMockInTestEnv:
    """In test/development environment, _get_client() returns a MagicMock (no network)."""

    def setup_method(self):
        _reset_firestore_client()

    def test_get_client_returns_mock_in_test_env(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "test")
        import core.config as config_module
        config_module.get_settings.cache_clear()
        config_module.settings = config_module.get_settings()

        _reset_firestore_client()
        from core.firestore_client import _get_client
        client = _get_client()
        assert client is not None
        # MagicMock is truthy and not a real Firestore client
        assert isinstance(client, MagicMock)

    @pytest.mark.asyncio
    async def test_get_document_returns_none_when_mock_snapshot_not_exists(self, monkeypatch):
        """In test env the client is a MagicMock; snapshot.exists == False → None returned."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        import core.config as config_module
        config_module.get_settings.cache_clear()
        config_module.settings = config_module.get_settings()

        _reset_firestore_client()

        # Arrange: mock the client chain so snapshot.exists is False
        mock_snapshot = MagicMock()
        mock_snapshot.exists = False
        mock_doc_ref = MagicMock()
        mock_doc_ref.get = AsyncMock(return_value=mock_snapshot)
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        import core.firestore_client as fc_module
        fc_module._fs_client = None
        mock_client = MagicMock()
        mock_client.collection.return_value = mock_collection
        fc_module._fs_client = mock_client

        from core.firestore_client import get_document
        result = await get_document("agent_performance", "test-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_document_returns_true_on_success(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "test")
        import core.config as config_module
        config_module.get_settings.cache_clear()
        config_module.settings = config_module.get_settings()

        _reset_firestore_client()

        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock(return_value=None)
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        import core.firestore_client as fc_module
        mock_client = MagicMock()
        mock_client.collection.return_value = mock_collection
        fc_module._fs_client = mock_client

        from core.firestore_client import set_document
        result = await set_document("agent_performance", "test-id", {"stat": 1})
        assert result is True


class TestFirestoreClientCircuitBreaker:
    """Circuit breaker opens after consecutive failures and returns safe defaults."""

    def setup_method(self):
        _reset_firestore_client()

    @pytest.mark.asyncio
    async def test_set_document_returns_false_when_circuit_open(self, monkeypatch):
        import core.firestore_client as fc_module
        # Force circuit open
        fc_module._breaker._failures = 10
        fc_module._breaker._opened_at = fc_module._breaker._time.time()

        from core.firestore_client import set_document
        result = await set_document("agent_performance", "test-id", {"stat": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_get_document_returns_none_when_circuit_open(self, monkeypatch):
        import core.firestore_client as fc_module
        # Force circuit open
        fc_module._breaker._failures = 10
        fc_module._breaker._opened_at = fc_module._breaker._time.time()

        from core.firestore_client import get_document
        result = await get_document("agent_performance", "test-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self, monkeypatch):
        """After _CIRCUIT_OPEN_THRESHOLD consecutive failures circuit opens."""
        import core.firestore_client as fc_module
        _reset_firestore_client()

        # Provide a mock client that always raises
        mock_doc_ref = MagicMock()
        mock_doc_ref.get = AsyncMock(side_effect=Exception("Firestore unavailable"))
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_client = MagicMock()
        mock_client.collection.return_value = mock_collection
        fc_module._fs_client = mock_client

        from core.firestore_client import get_document, _CIRCUIT_OPEN_THRESHOLD
        for _ in range(_CIRCUIT_OPEN_THRESHOLD):
            await get_document("agent_performance", "x")

        assert fc_module._breaker.is_open() is True

    @pytest.mark.asyncio
    async def test_circuit_resets_after_timeout(self, monkeypatch):
        import core.firestore_client as fc_module
        _reset_firestore_client()

        # Open the circuit but backdate opened_at beyond reset window
        fc_module._breaker._failures = 10
        fc_module._breaker._opened_at = fc_module._breaker._time.time() - 60  # 60s ago

        # Circuit should auto-reset on next is_open() call
        assert fc_module._breaker.is_open() is False
