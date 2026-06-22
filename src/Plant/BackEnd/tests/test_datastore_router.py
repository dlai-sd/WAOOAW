"""Unit tests for DatastoreRouter (INFRA-ROUTING-1 S1)."""

import pytest
from pydantic import ValidationError


def _reload_settings(monkeypatch, mode: str):
    """Helper: clear the lru_cache and reload settings with a new DATA_ROUTER_MODE."""
    monkeypatch.setenv("DATA_ROUTER_MODE", mode)
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()
    # Re-patch the singleton that datastore_router reads from
    import core.datastore_router as dr_module
    # DatastoreRouter.mode property reads settings at call time — no reload needed.
    return config_module.settings


class TestDatastoreRouterModes:
    """DatastoreRouter routing decisions for each mode."""

    def test_reads_from_firestore_false_in_sql_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "sql")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.reads_from_firestore("agent_performance") is False

    def test_writes_to_firestore_false_in_sql_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "sql")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.writes_to_firestore("agent_performance") is False

    def test_writes_to_firestore_true_in_dual_write_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "dual_write")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.writes_to_firestore("agent_performance") is True

    def test_reads_from_firestore_false_in_dual_write_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "dual_write")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        # dual_write reads from SQL, not Firestore
        assert router.reads_from_firestore("agent_performance") is False

    def test_reads_from_firestore_true_in_firestore_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "firestore")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.reads_from_firestore("agent_performance") is True

    def test_writes_to_firestore_true_in_shadow_read_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "shadow_read")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.writes_to_firestore("agent_performance") is True

    def test_shadow_mode_true_in_shadow_read_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "shadow_read")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.shadow_mode("agent_performance") is True

    def test_shadow_mode_false_in_dual_write_mode(self, monkeypatch):
        _reload_settings(monkeypatch, "dual_write")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.shadow_mode("agent_performance") is False

    def test_non_routable_entity_always_returns_false(self, monkeypatch):
        """customer is not in _ROUTABLE_COLLECTIONS — must return False for all modes."""
        for mode in ("sql", "dual_write", "shadow_read", "firestore"):
            _reload_settings(monkeypatch, mode)
            from core.datastore_router import DatastoreRouter
            router = DatastoreRouter()
            assert router.reads_from_firestore("customer") is False
            assert router.writes_to_firestore("customer") is False

    def test_is_routable_agent_performance(self, monkeypatch):
        _reload_settings(monkeypatch, "sql")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.is_routable("agent_performance") is True

    def test_is_routable_agent_availability(self, monkeypatch):
        _reload_settings(monkeypatch, "sql")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.is_routable("agent_availability") is True

    def test_is_routable_unknown_collection(self, monkeypatch):
        _reload_settings(monkeypatch, "sql")
        from core.datastore_router import DatastoreRouter
        router = DatastoreRouter()
        assert router.is_routable("payment") is False

    def test_module_singleton_importable(self):
        from core.datastore_router import DatastoreRouter, datastore_router
        assert isinstance(datastore_router, DatastoreRouter)


class TestSettingsDataRouterModeValidation:
    """Settings rejects unknown data_router_mode values."""

    def test_valid_modes_accepted(self, monkeypatch):
        import core.config as config_module
        for mode in ("sql", "dual_write", "shadow_read", "firestore"):
            monkeypatch.setenv("DATA_ROUTER_MODE", mode)
            config_module.get_settings.cache_clear()
            settings = config_module.get_settings()
            assert settings.data_router_mode == mode

    def test_invalid_mode_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv("DATA_ROUTER_MODE", "postgres_only")
        import core.config as config_module
        config_module.get_settings.cache_clear()
        with pytest.raises((ValidationError, ValueError)):
            config_module.get_settings()

    def test_default_mode_is_sql(self, monkeypatch):
        monkeypatch.delenv("DATA_ROUTER_MODE", raising=False)
        import core.config as config_module
        config_module.get_settings.cache_clear()
        settings = config_module.get_settings()
        assert settings.data_router_mode == "sql"
