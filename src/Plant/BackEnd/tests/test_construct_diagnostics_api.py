"""Tests for construct diagnostics API endpoints (PLANT-MOULD-1 E4)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_client():
    """Build a TestClient with DB dependencies overridden to avoid real Postgres."""
    from main import app
    from core.database import get_read_db_session

    async def _fake_db():
        """Yield a mock AsyncSession that returns empty results for all queries."""
        mock_session = AsyncMock()
        # Default: scalars().all() → [], scalar_one_or_none() → None, scalar() → 0
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalar.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# construct-health tests
# ---------------------------------------------------------------------------


def test_construct_health_returns_404_for_unknown_hire():
    """GET /api/v1/v1/hired-agents/{id}/construct-health → 404 for unknown ID."""
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/v1/hired-agents/unknown-hire-id/construct-health",
            headers={"X-Correlation-ID": "test-cid-1"},
        )
        assert resp.status_code == 404


def test_construct_health_returns_200_for_known_hire():
    """GET construct-health returns 200 + ConstructHealthResponse for a valid hire."""
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_with_hire():
        mock_session = AsyncMock()

        def _execute_side_effect(query):
            # Check if the query is for hired_agent existence
            # Return a mock that has a scalar() that returns "hire-001"
            mock_result = MagicMock()
            mock_result.scalar.return_value = "hire-001"
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        mock_session.execute = AsyncMock(side_effect=lambda q: _execute_side_effect(q))
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_with_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/v1/hired-agents/hire-001/construct-health",
            headers={"X-Correlation-ID": "test-cid-2"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["hired_agent_id"] == "hire-001"
        assert "scheduler" in body
        assert "connector" in body
        assert "policy" in body

    app.dependency_overrides.clear()


def test_secret_ref_masking():
    """secret_ref in connector section shows only last 4 chars."""
    from api.v1.construct_diagnostics import _mask_secret_ref

    result = _mask_secret_ref("ABCDE12345")
    assert result == "****2345"


def test_mask_secret_ref_short():
    from api.v1.construct_diagnostics import _mask_secret_ref
    # Shorter than 4 chars returned as-is
    assert _mask_secret_ref("AB") == "AB"
    assert _mask_secret_ref("") == ""


# ---------------------------------------------------------------------------
# scheduler-diagnostics tests
# ---------------------------------------------------------------------------


def test_scheduler_diagnostics_returns_404_for_unknown():
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/v1/hired-agents/no-such-id/scheduler-diagnostics",
            headers={"X-Correlation-ID": "test-cid-3"},
        )
        assert resp.status_code == 404


def test_scheduler_diagnostics_returns_200_for_known():
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_hire():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "hire-002"
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/v1/hired-agents/hire-002/scheduler-diagnostics",
            headers={"X-Correlation-ID": "test-cid-4"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["hired_agent_id"] == "hire-002"
        assert "dlq_depth" in body
        assert "dlq_entries" in body

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DLQ endpoint tests
# ---------------------------------------------------------------------------


def test_dlq_endpoint_returns_empty_list_when_no_entries():
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/v1/ops/dlq",
            headers={"X-Correlation-ID": "test-cid-5"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


def test_dlq_endpoint_accepts_hired_agent_id_filter():
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/v1/ops/dlq?hired_agent_id=ha-xyz",
            headers={"X-Correlation-ID": "test-cid-6"},
        )
        assert resp.status_code == 200


def test_dlq_error_message_truncated_at_200_chars():
    """DLQEntry.error_message must be <= 200 chars."""
    from api.v1.construct_diagnostics import DLQEntry

    long_message = "x" * 500
    entry = DLQEntry(
        dlq_id="d-1",
        hired_agent_id="ha-1",
        failed_at="2026-01-01T00:00:00",
        hook_stage="unknown",
        error_message=long_message[:200],
    )
    assert len(entry.error_message) == 200


def test_construct_diagnostics_routes_use_read_db_session():
    """Verify construct_diagnostics routes depend on get_read_db_session (not get_db_session)."""
    import inspect
    from api.v1.construct_diagnostics import get_construct_health, get_scheduler_diagnostics, list_dlq_entries
    from core.database import get_read_db_session, get_db_session

    for endpoint_fn in (get_construct_health, get_scheduler_diagnostics, list_dlq_entries):
        sig = inspect.signature(endpoint_fn)
        for param in sig.parameters.values():
            dep = getattr(param.default, "dependency", None)
            if dep is get_db_session:
                pytest.fail(
                    f"{endpoint_fn.__name__} uses get_db_session instead of get_read_db_session"
                )
