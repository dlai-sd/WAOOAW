"""Unit tests for POST /api/v1/otp/sessions (registration OTP creation).

Critical behaviours under test:

A. Environment detection (_is_dev_mode)
   A1. ENVIRONMENT=demo  → production mode (email sent, no otp_code in response)
   A2. ENVIRONMENT=uat   → production mode (email sent)
   A3. ENVIRONMENT=prod  → production mode (email sent)
   A4. ENVIRONMENT=""    → dev mode (no email, otp_code echoed)
   A5. ENVIRONMENT=local → dev mode (no email, otp_code echoed)

B. Email dispatch in production (demo/uat/prod)
   B1. Email enqueued via BackgroundTasks when channel=email + prod mode
   B2. No email enqueued when channel=phone (SMS not supported yet)
   B3. otp_code NOT present in 201 response body in prod mode

C. Email dispatch in dev mode
   C1. No email enqueued when dev mode
   C2. otp_code IS present in 201 response body in dev mode

D. _enqueue_otp_email Celery fallback
   D1. When broker available: send_otp_email.delay() is called
   D2. When broker raises (unavailable): falls back to send_otp_email.apply()
   D3. When both raise: logs exception, does not propagate

E. OTP session DB writes
   E1. INSERT into otp_sessions is executed
   E2. Previous unexpired sessions for same destination are invalidated (UPDATE)

F. Response contract
   F1. 201 with otp_id, destination_masked, expires_in_seconds
   F2. destination_masked hides middle chars of email
"""
from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ── App factory ───────────────────────────────────────────────────────────────

def _make_app(db_mock: AsyncMock) -> FastAPI:
    """Build a minimal FastAPI app with the otp router and a mocked DB session."""
    from api.v1.otp import router
    from core.database import get_db_session

    app = FastAPI()
    app.dependency_overrides[get_db_session] = lambda: db_mock
    app.include_router(router, prefix="/api/v1")
    return app


def _db_mock() -> AsyncMock:
    """Return a mock AsyncSession that commits and executes without error."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.commit = AsyncMock()
    return db


_OTP_PAYLOAD = {
    "registration_id": "user@example.com",
    "channel": "email",
    "destination": "user@example.com",
}

# ── A: Environment detection ─────────────────────────────────────────────────

@pytest.mark.parametrize("env_value,expected_dev", [
    ("demo",       False),  # A1 — demo is production
    ("uat",        False),  # A2
    ("prod",       False),  # A3
    ("production", False),
    ("",           True),   # A4 — empty → dev
    ("local",      True),   # A5
    ("test",       True),
    ("development",True),
])
def test_is_dev_mode(env_value, expected_dev):
    """_is_dev_mode() must return False for demo/uat/prod and True for everything else."""
    from api.v1.otp import _is_dev_mode
    with patch.dict(os.environ, {"ENVIRONMENT": env_value}, clear=False):
        assert _is_dev_mode() is expected_dev, f"ENVIRONMENT={env_value!r}: expected dev={expected_dev}"


# ── B: Email dispatch in production ──────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("env", ["demo", "uat", "prod"])
async def test_email_enqueued_in_production_envs(env):
    """B1: BackgroundTask is added for email channel in production environments."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": env}), \
         patch("api.v1.otp._enqueue_otp_email") as mock_enqueue:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    assert r.status_code == 201, r.text
    # BackgroundTasks runs _enqueue_otp_email; validate it was scheduled
    mock_enqueue.assert_called_once()
    call_kwargs = mock_enqueue.call_args.kwargs
    assert call_kwargs["to_email"] == "user@example.com"
    assert len(call_kwargs["otp_code"]) == 6


@pytest.mark.asyncio
async def test_email_not_enqueued_for_phone_channel():
    """B2: No email enqueued when channel=phone."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": "demo"}), \
         patch("api.v1.otp._enqueue_otp_email") as mock_enqueue:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post(
                "/api/v1/otp/sessions",
                json={**_OTP_PAYLOAD, "channel": "phone", "destination": "+919876543210"},
            )

    assert r.status_code == 201
    mock_enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_otp_code_not_in_response_in_production():
    """B3: otp_code must be absent (None) in production response."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": "demo"}), \
         patch("api.v1.otp._enqueue_otp_email"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    assert r.status_code == 201
    assert r.json().get("otp_code") is None, "otp_code must never be exposed in production"


# ── C: Dev mode behaviour ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_email_not_enqueued_in_dev_mode():
    """C1: No email background task in dev / empty environment."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}, clear=False), \
         patch("api.v1.otp._enqueue_otp_email") as mock_enqueue:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    assert r.status_code == 201
    mock_enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_otp_code_echoed_in_dev_mode():
    """C2: otp_code is present in response body in dev mode (for local/CI use)."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}, clear=False):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    assert r.status_code == 201
    code = r.json().get("otp_code")
    assert code is not None, "otp_code should be echoed in dev mode"
    assert len(code) == 6
    assert code.isdigit()


# ── D: _enqueue_otp_email Celery fallback ────────────────────────────────────
# celery is not installed in the test venv.  The production import is lazy
# (`from worker.tasks.email_tasks import send_otp_email` inside the function
# body), so we satisfy it by pre-populating sys.modules with mocks.

def _worker_sys_modules(mock_task: MagicMock) -> dict:
    """Build a sys.modules patch dict that makes `worker` importable without celery."""
    mock_email_tasks = MagicMock()
    mock_email_tasks.send_otp_email = mock_task
    return {
        "celery": MagicMock(),
        "worker": MagicMock(),
        "worker.tasks": MagicMock(),
        "worker.tasks.email_tasks": mock_email_tasks,
    }


_ENQUEUE_KWARGS = dict(
    to_email="x@example.com",
    otp_code="123456",
    expires_in_seconds=300,
    otp_id="test-otp-id",
    expires_at_iso="2026-03-01T00:00:00+00:00",
)


def test_enqueue_uses_celery_delay_when_broker_available():
    """D1: When broker is reachable, .delay() is called."""
    mock_task = MagicMock()

    with patch.dict(sys.modules, _worker_sys_modules(mock_task)):
        # Reload so the module picks up the patched sys.modules
        import api.v1.otp as _otp_mod
        importlib.reload(_otp_mod)
        from api.v1.otp import _enqueue_otp_email
        _enqueue_otp_email(**_ENQUEUE_KWARGS)

    mock_task.delay.assert_called_once()


def test_enqueue_falls_back_to_apply_when_broker_unavailable():
    """D2: When .delay() raises (no broker), .apply() is invoked as fallback."""
    mock_task = MagicMock()
    mock_task.delay = MagicMock(side_effect=Exception("Redis connection refused"))

    with patch.dict(sys.modules, _worker_sys_modules(mock_task)):
        import api.v1.otp as _otp_mod
        importlib.reload(_otp_mod)
        from api.v1.otp import _enqueue_otp_email
        _enqueue_otp_email(**_ENQUEUE_KWARGS)

    mock_task.delay.assert_called_once()
    mock_task.apply.assert_called_once()
    apply_kwargs = mock_task.apply.call_args.kwargs["kwargs"]
    assert apply_kwargs["to_email"] == "x@example.com"
    assert apply_kwargs["otp_code"] == "123456"


def test_enqueue_logs_exception_when_both_celery_and_apply_fail():
    """D3: When both .delay() and .apply() raise, exception is logged (not propagated)."""
    mock_task = MagicMock()
    mock_task.delay = MagicMock(side_effect=Exception("no broker"))
    mock_task.apply = MagicMock(side_effect=Exception("apply also failed"))

    with patch.dict(sys.modules, _worker_sys_modules(mock_task)):
        import api.v1.otp as _otp_mod
        importlib.reload(_otp_mod)
        from api.v1.otp import _enqueue_otp_email
        with patch("api.v1.otp.logger") as mock_logger:
            # Must not raise
            _enqueue_otp_email(**_ENQUEUE_KWARGS)

    mock_logger.exception.assert_called_once()


# ── E: DB writes ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_otp_session_inserts_into_db():
    """E1: An INSERT into otp_sessions is executed on every request."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}), \
         patch("api.v1.otp._enqueue_otp_email"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    # db.execute should be called at least twice: UPDATE (invalidate old) + INSERT
    assert db.execute.call_count >= 2
    all_sql = " ".join(
        str(c.args[0]) for c in db.execute.call_args_list if c.args
    )
    assert "INSERT" in all_sql.upper()


@pytest.mark.asyncio
async def test_previous_sessions_invalidated():
    """E2: An UPDATE is executed before INSERT to expire old sessions for same destination."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}), \
         patch("api.v1.otp._enqueue_otp_email"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    all_sql = " ".join(
        str(c.args[0]) for c in db.execute.call_args_list if c.args
    )
    assert "UPDATE" in all_sql.upper()


@pytest.mark.asyncio
async def test_db_commit_called():
    """E1b: db.commit() is called after the INSERT."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}), \
         patch("api.v1.otp._enqueue_otp_email"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    db.commit.assert_called_once()


# ── F: Response contract ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_response_shape_and_status():
    """F1: 201 response contains otp_id (uuid), destination_masked, expires_in_seconds."""
    import uuid
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/v1/otp/sessions", json=_OTP_PAYLOAD)

    assert r.status_code == 201
    body = r.json()
    assert "otp_id" in body
    uuid.UUID(body["otp_id"])  # must be valid UUID
    assert "destination_masked" in body
    assert "expires_in_seconds" in body
    assert body["expires_in_seconds"] > 0


@pytest.mark.asyncio
async def test_destination_masked_hides_email():
    """F2: Email destination is partially masked (not returned verbatim)."""
    db = _db_mock()
    app = _make_app(db)

    with patch.dict(os.environ, {"ENVIRONMENT": ""}):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post(
                "/api/v1/otp/sessions",
                json={**_OTP_PAYLOAD, "destination": "priya@example.com"},
            )

    assert r.status_code == 201
    masked = r.json()["destination_masked"]
    # Should not be the full email
    assert masked != "priya@example.com"
    # Should still contain the domain portion
    assert "example.com" in masked
    # Should contain masking chars
    assert "*" in masked
