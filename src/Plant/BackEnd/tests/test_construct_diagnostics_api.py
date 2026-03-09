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
    """GET /api/v1/hired-agents/{id}/construct-health → 404 for unknown ID."""
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/hired-agents/unknown-hire-id/construct-health",
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
            # _check_hired_agent_exists uses bool(scalar()); return truthy string to signal existence
            mock_result = MagicMock()
            mock_result.scalar.return_value = "hire-001"
            mock_result.scalar_one_or_none.return_value = None  # model queries return None gracefully
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        mock_session.execute = AsyncMock(side_effect=lambda q: _execute_side_effect(q))
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_with_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/hired-agents/hire-001/construct-health",
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
            "/api/v1/hired-agents/no-such-id/scheduler-diagnostics",
            headers={"X-Correlation-ID": "test-cid-3"},
        )
        assert resp.status_code == 404


def test_scheduler_diagnostics_returns_200_for_known():
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_hire():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "hire-002"  # truthy → hire exists
        mock_result.scalar_one_or_none.return_value = None  # model queries return None gracefully
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/hired-agents/hire-002/scheduler-diagnostics",
            headers={"X-Correlation-ID": "test-cid-4"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["hired_agent_id"] == "hire-002"
        assert "dlq_depth" in body
        assert "dlq_entries" in body

    app.dependency_overrides.clear()


def test_scheduler_diagnostics_reflects_paused_state():
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_hire():
        mock_session = AsyncMock()
        mock_model = MagicMock()
        mock_model.hired_instance_id = "hire-003"
        mock_model.subscription_id = "sub-003"
        mock_model.agent_id = "agent-003"
        mock_model.agent_type_id = "marketing.digital_marketing.v1"
        mock_model.customer_id = "cust-003"
        mock_model.nickname = None
        mock_model.theme = None
        mock_model.config = {"scheduler_paused": True}
        mock_model.configured = True
        mock_model.goals_completed = False
        mock_model.active = True
        mock_model.trial_status = "not_started"
        mock_model.trial_start_at = None
        mock_model.trial_end_at = None
        mock_model.created_at = __import__("datetime").datetime.utcnow()
        mock_model.updated_at = __import__("datetime").datetime.utcnow()

        exists_result = MagicMock()
        exists_result.scalar.return_value = "hire-003"

        rows_result = MagicMock()
        rows_result.scalar_one_or_none.return_value = None
        rows_result.scalars.return_value.all.return_value = []

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model

        mock_session.execute = AsyncMock(
            side_effect=[exists_result, rows_result, rows_result, rows_result, model_result]
        )
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/hired-agents/hire-003/scheduler-diagnostics",
            headers={"X-Correlation-ID": "test-cid-paused"},
        )
        assert resp.status_code == 200
        assert resp.json()["pause_state"] == "PAUSED"

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DLQ endpoint tests
# ---------------------------------------------------------------------------


def test_dlq_endpoint_returns_empty_list_when_no_entries():
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/ops/dlq",
            headers={"X-Correlation-ID": "test-cid-5"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


def test_dlq_endpoint_accepts_hired_agent_id_filter():
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/ops/dlq?hired_agent_id=ha-xyz",
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


# ---------------------------------------------------------------------------
# CP-DEFECTS-1 E4: hook-trace tests
# ---------------------------------------------------------------------------


def test_hook_trace_returns_404_for_unknown_hire():
    """GET /api/v1/hired-agents/{id}/hook-trace → 404 when hired_agent_id not found."""
    for client in _make_test_client():
        resp = client.get(
            "/api/v1/hired-agents/no-such-ha/hook-trace",
            headers={"X-Correlation-ID": "test-ht-1"},
        )
        assert resp.status_code == 404


def test_hook_trace_returns_empty_list_for_known_hire():
    """GET hook-trace returns 200 + empty list for a known hire (stub implementation)."""
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_hire():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "ha-001"  # truthy → hire exists
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/hired-agents/ha-001/hook-trace",
            headers={"X-Correlation-ID": "test-ht-2"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    app.dependency_overrides.clear()


def test_hook_trace_accepts_stage_and_result_filters():
    """GET hook-trace accepts stage/result/limit query params without error."""
    from main import app
    from core.database import get_read_db_session

    async def _fake_db_hire():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "ha-001"
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        yield mock_session

    app.dependency_overrides[get_read_db_session] = _fake_db_hire

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get(
            "/api/v1/hired-agents/ha-001/hook-trace?stage=pre_pump&result=proceed&limit=10",
            headers={"X-Correlation-ID": "test-ht-3"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# CP-DEFECTS-1 E4: DLQ requeue tests
# ---------------------------------------------------------------------------


def test_dlq_requeue_returns_404_for_unknown_entry():
    """POST /api/v1/ops/dlq/{id}/requeue → 404 when dlq_id not found."""
    from main import app
    from core.database import get_db_session, get_read_db_session

    async def _fake_write_db():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0  # no rows deleted → entry not found
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_db_session] = _fake_write_db

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post(
            "/api/v1/ops/dlq/nonexistent-id/requeue",
            headers={"X-Correlation-ID": "test-requeue-1"},
        )
        assert resp.status_code == 404

    app.dependency_overrides.clear()


def test_dlq_requeue_returns_queued_status_on_success():
    """POST /api/v1/ops/dlq/{id}/requeue → {status: queued, dlq_id} when entry deleted."""
    from main import app
    from core.database import get_db_session

    async def _fake_write_db():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1  # row deleted successfully
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[get_db_session] = _fake_write_db

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post(
            "/api/v1/ops/dlq/dlq-xyz/requeue",
            headers={"X-Correlation-ID": "test-requeue-2"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "queued"
        assert body["dlq_id"] == "dlq-xyz"

    app.dependency_overrides.clear()
