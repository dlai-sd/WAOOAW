"""Unit tests for shadow_compare (INFRA-ROUTING-1 It2 S1)."""

import types
import uuid
import pytest
from unittest.mock import AsyncMock, patch


def _set_router_mode(monkeypatch, mode: str):
    """Patch DATA_ROUTER_MODE and reload settings singleton."""
    monkeypatch.setenv("DATA_ROUTER_MODE", mode)
    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()


def _mock_stat(posts_published: int = 5):
    """Return a minimal stat-like object with metrics."""
    return types.SimpleNamespace(
        metrics={"posts_published": posts_published, "impressions": 100}
    )


class TestShadowCompareNoopModes:
    """shadow_compare is a no-op in sql and dual_write modes."""

    @pytest.mark.asyncio
    async def test_noop_in_sql_mode(self, monkeypatch):
        _set_router_mode(monkeypatch, "sql")
        from services.performance_stat_router import shadow_compare

        with patch("services.performance_stat_router.get_document", new_callable=AsyncMock) as mock_get:
            await shadow_compare(uuid.uuid4(), _mock_stat())
            mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_in_dual_write_mode(self, monkeypatch):
        _set_router_mode(monkeypatch, "dual_write")
        from services.performance_stat_router import shadow_compare

        with patch("services.performance_stat_router.get_document", new_callable=AsyncMock) as mock_get:
            await shadow_compare(uuid.uuid4(), _mock_stat())
            mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_in_firestore_mode(self, monkeypatch):
        _set_router_mode(monkeypatch, "firestore")
        from services.performance_stat_router import shadow_compare

        with patch("services.performance_stat_router.get_document", new_callable=AsyncMock) as mock_get:
            await shadow_compare(uuid.uuid4(), _mock_stat())
            mock_get.assert_not_called()


class TestShadowCompareDriftDetection:
    """shadow_compare increments drift counter on mismatch in shadow_read mode."""

    @pytest.mark.asyncio
    async def test_increments_shadow_reads_counter(self, monkeypatch):
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()
        fs_doc = {"posts_count": 5, "hired_instance_id": str(hired_id)}

        from services.performance_stat_router import shadow_compare
        from core.metrics import firestore_shadow_reads_total

        before = firestore_shadow_reads_total.labels(
            collection="agent_performance"
        )._value.get()

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            return_value=fs_doc,
        ):
            await shadow_compare(hired_id, _mock_stat(posts_published=5))

        after = firestore_shadow_reads_total.labels(
            collection="agent_performance"
        )._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_increments_drift_counter_on_mismatch(self, monkeypatch):
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()
        # Firestore has 3, SQL has 5 → mismatch
        fs_doc = {"posts_count": 3, "hired_instance_id": str(hired_id)}

        from services.performance_stat_router import shadow_compare
        from core.metrics import firestore_drift_total

        before = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            return_value=fs_doc,
        ):
            await shadow_compare(hired_id, _mock_stat(posts_published=5))

        after = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_no_drift_counter_when_values_match(self, monkeypatch):
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()
        # Firestore and SQL both have 5 → no drift
        fs_doc = {"posts_count": 5}

        from services.performance_stat_router import shadow_compare
        from core.metrics import firestore_drift_total

        before = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            return_value=fs_doc,
        ):
            await shadow_compare(hired_id, _mock_stat(posts_published=5))

        after = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()
        assert after == before  # no increment

    @pytest.mark.asyncio
    async def test_no_drift_when_firestore_doc_absent(self, monkeypatch):
        """When Firestore has no document yet, shadow_compare returns without incrementing drift."""
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()

        from services.performance_stat_router import shadow_compare
        from core.metrics import firestore_drift_total

        before = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await shadow_compare(hired_id, _mock_stat())

        after = firestore_drift_total.labels(
            collection="agent_performance"
        )._value.get()
        assert after == before


class TestShadowCompareNeverRaises:
    """shadow_compare must never propagate exceptions — shadow mode is invisible to callers."""

    @pytest.mark.asyncio
    async def test_does_not_raise_on_get_document_exception(self, monkeypatch):
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()

        from services.performance_stat_router import shadow_compare

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Firestore unavailable"),
        ):
            # Must not raise
            await shadow_compare(hired_id, _mock_stat())

    @pytest.mark.asyncio
    async def test_does_not_raise_on_bad_stat_object(self, monkeypatch):
        _set_router_mode(monkeypatch, "shadow_read")
        hired_id = uuid.uuid4()
        # stat has no metrics attribute at all
        bad_stat = object()
        fs_doc = {"posts_count": 5}

        from services.performance_stat_router import shadow_compare

        with patch(
            "services.performance_stat_router.get_document",
            new_callable=AsyncMock,
            return_value=fs_doc,
        ):
            await shadow_compare(hired_id, bad_stat)
