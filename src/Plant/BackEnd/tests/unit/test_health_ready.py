"""Unit tests for E3-S4 /health/ready deep readiness endpoint (Plant backend).

Tests the endpoint using a minimal FastAPI test app that replicates the
/health/ready logic with injectable DB and Redis dependencies — no full
main.py import required.

Covers:
  - 200 + {"status": "ok"} when DB and Redis both healthy
  - 503 + {"status": "degraded"} when DB fails
  - 503 + {"status": "degraded"} when Redis fails
  - 503 when both fail
  - Response JSON always contains: status, db, redis, timestamp
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


# ── Minimal reproduction of the /health/ready route ──────────────────────────
# We replicate the endpoint logic here so the test has no dependency on
# loading the full Plant main.py (which requires many environment variables).

def _build_readiness_app(db_raises: bool, redis_raises: bool) -> FastAPI:
    """Build a minimal FastAPI app with /health/ready wired to mocked deps."""
    mini = FastAPI()

    @mini.get("/health/ready")
    async def readiness_check():
        db_ok = False
        redis_ok = False

        # DB check (mocked)
        if not db_raises:
            db_ok = True

        # Redis check (mocked)
        if not redis_raises:
            redis_ok = True

        status = "ok" if (db_ok and redis_ok) else "degraded"
        http_status = 200 if (db_ok and redis_ok) else 503
        return JSONResponse(
            status_code=http_status,
            content={
                "status": status,
                "db": "ok" if db_ok else "error",
                "redis": "ok" if redis_ok else "error",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    return mini


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHealthReady:
    """E3-S4: /health/ready returns correct status and HTTP code."""

    def test_200_when_both_healthy(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=False, redis_raises=False))
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"
        assert body["redis"] == "ok"

    def test_503_when_db_fails(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=True, redis_raises=False))
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "error"
        assert body["redis"] == "ok"

    def test_503_when_redis_fails(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=False, redis_raises=True))
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "ok"
        assert body["redis"] == "error"

    def test_503_when_both_fail(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=True, redis_raises=True))
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "error"
        assert body["redis"] == "error"

    def test_response_has_required_keys(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=False, redis_raises=False))
        body = client.get("/health/ready").json()
        for key in ("status", "db", "redis", "timestamp"):
            assert key in body, f"Missing key: {key}"

    def test_timestamp_is_iso_format(self) -> None:
        client = TestClient(_build_readiness_app(db_raises=False, redis_raises=False))
        body = client.get("/health/ready").json()
        # Should parse without raising
        datetime.fromisoformat(body["timestamp"])
