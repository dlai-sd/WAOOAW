"""Unit tests for reconciliation_service (INFRA-ROUTING-1 It2 S2)."""

import types
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_stat(posts_published: int = 5, stat_id: str | None = None):
    """Build a minimal PerformanceStatModel-like object for testing."""
    return types.SimpleNamespace(
        id=stat_id or str(uuid.uuid4()),
        hired_instance_id=str(uuid.uuid4()),
        metrics={"posts_published": posts_published},
    )


def _make_db_with_stats(stats: list):
    """Return a mock AsyncSession that yields the given stats list from execute()."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = stats
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result_mock)
    return db


class TestReconciliationSweepDetectsDrift:
    """run_reconciliation_sweep identifies drifted rows and calls after_stat_write."""

    @pytest.mark.asyncio
    async def test_returns_correct_summary_fields(self):
        db = _make_db_with_stats([])
        from services.reconciliation_service import run_reconciliation_sweep

        result = await run_reconciliation_sweep(db)

        assert "total_checked" in result
        assert "drifted" in result
        assert "repaired" in result
        assert "errors" in result
        assert "run_at" in result

    @pytest.mark.asyncio
    async def test_no_drift_when_values_match(self):
        stat = _make_stat(posts_published=7)
        db = _make_db_with_stats([stat])
        # Firestore matches SQL: posts_count == 7
        fs_doc = {"posts_count": 7}

        from services.reconciliation_service import run_reconciliation_sweep

        with (
            patch("services.reconciliation_service.get_document", new_callable=AsyncMock, return_value=fs_doc),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=True) as mock_write,
        ):
            result = await run_reconciliation_sweep(db)

        assert result["total_checked"] == 1
        assert result["drifted"] == 0
        assert result["repaired"] == 0
        mock_write.assert_not_called()

    @pytest.mark.asyncio
    async def test_detects_drift_and_calls_after_stat_write(self):
        stat = _make_stat(posts_published=5)
        db = _make_db_with_stats([stat])
        # Firestore has 3, SQL has 5 → drift
        fs_doc = {"posts_count": 3}

        from services.reconciliation_service import run_reconciliation_sweep
        from core.metrics import firestore_drift_total

        before = firestore_drift_total.labels(collection="agent_performance")._value.get()

        with (
            patch("services.reconciliation_service.get_document", new_callable=AsyncMock, return_value=fs_doc),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=True) as mock_write,
        ):
            result = await run_reconciliation_sweep(db)

        assert result["total_checked"] == 1
        assert result["drifted"] == 1
        assert result["repaired"] == 1
        mock_write.assert_called_once_with(stat.hired_instance_id, stat)

        after = firestore_drift_total.labels(collection="agent_performance")._value.get()
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_detects_drift_when_firestore_has_no_doc(self):
        stat = _make_stat(posts_published=5)
        db = _make_db_with_stats([stat])

        from services.reconciliation_service import run_reconciliation_sweep

        with (
            patch("services.reconciliation_service.get_document", new_callable=AsyncMock, return_value=None),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=True) as mock_write,
        ):
            result = await run_reconciliation_sweep(db)

        # fs_posts is None, sql_posts is 5 → drift
        assert result["drifted"] == 1
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_counts_repaired_when_after_stat_write_succeeds(self):
        stat = _make_stat(posts_published=5)
        db = _make_db_with_stats([stat])
        fs_doc = {"posts_count": 0}

        from services.reconciliation_service import run_reconciliation_sweep

        with (
            patch("services.reconciliation_service.get_document", new_callable=AsyncMock, return_value=fs_doc),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=True),
        ):
            result = await run_reconciliation_sweep(db)

        assert result["repaired"] == 1

    @pytest.mark.asyncio
    async def test_counts_not_repaired_when_after_stat_write_fails(self):
        stat = _make_stat(posts_published=5)
        db = _make_db_with_stats([stat])
        fs_doc = {"posts_count": 0}

        from services.reconciliation_service import run_reconciliation_sweep

        with (
            patch("services.reconciliation_service.get_document", new_callable=AsyncMock, return_value=fs_doc),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=False),
        ):
            result = await run_reconciliation_sweep(db)

        assert result["drifted"] == 1
        assert result["repaired"] == 0


class TestReconciliationSweepHandlesErrorsGracefully:
    """run_reconciliation_sweep catches per-row errors and counts them."""

    @pytest.mark.asyncio
    async def test_counts_errors_and_does_not_raise(self):
        stat = _make_stat()
        db = _make_db_with_stats([stat])

        from services.reconciliation_service import run_reconciliation_sweep

        with patch(
            "services.reconciliation_service.get_document",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Firestore exploded"),
        ):
            result = await run_reconciliation_sweep(db)

        assert result["errors"] == 1
        assert result["total_checked"] == 1
        # Function must not raise — errors are captured, not propagated.

    @pytest.mark.asyncio
    async def test_processes_remaining_rows_after_error(self):
        stat_ok = _make_stat(posts_published=5)
        stat_bad = _make_stat(posts_published=3)
        db = _make_db_with_stats([stat_ok, stat_bad])

        # First call raises, second returns matching doc
        import asyncio as _asyncio

        call_count = 0

        async def get_doc_side_effect(collection, doc_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("transient error")
            return {"posts_count": 3}  # matches stat_bad

        from services.reconciliation_service import run_reconciliation_sweep

        with (
            patch("services.reconciliation_service.get_document", side_effect=get_doc_side_effect),
            patch("services.reconciliation_service.after_stat_write", new_callable=AsyncMock, return_value=True),
        ):
            result = await run_reconciliation_sweep(db)

        assert result["total_checked"] == 2
        assert result["errors"] == 1
        assert result["drifted"] == 0  # stat_bad matches (posts_count==3 == posts_published==3)
