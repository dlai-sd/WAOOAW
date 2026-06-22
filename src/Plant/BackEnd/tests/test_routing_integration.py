"""
Integration tests for INFRA-ROUTING-1 dual-path data router.

Tests all four routing modes without live GCP credentials.
Firestore calls are intercepted by the mock client (ENVIRONMENT=test).
"""

import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(autouse=True)
def reset_router_mode(monkeypatch):
    """Reset DATA_ROUTER_MODE to sql after each test."""
    yield
    monkeypatch.setenv("DATA_ROUTER_MODE", "sql")


def set_mode(monkeypatch, mode: str):
    monkeypatch.setenv("DATA_ROUTER_MODE", mode)
    # Force settings re-read
    from core import config as cfg_mod
    cfg_mod.get_settings.cache_clear()
    cfg_mod.settings = cfg_mod.get_settings()


@pytest.mark.asyncio
async def test_sql_mode_no_firestore_call(monkeypatch):
    set_mode(monkeypatch, "sql")
    from services.performance_stat_router import after_stat_write
    with patch("services.performance_stat_router.set_document", new_callable=AsyncMock) as mock_set:
        await after_stat_write(uuid4(), object())
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_dual_write_mode_calls_firestore(monkeypatch):
    set_mode(monkeypatch, "dual_write")
    from services.performance_stat_router import after_stat_write
    with patch("services.performance_stat_router.set_document", new_callable=AsyncMock, return_value=True) as mock_set:
        await after_stat_write(uuid4(), object())
        mock_set.assert_called_once()


@pytest.mark.asyncio
async def test_firestore_mode_reads_from_firestore(monkeypatch):
    set_mode(monkeypatch, "firestore")
    hired_id = uuid4()
    from services.performance_stat_router import read_stat_from_firestore
    with patch("services.performance_stat_router.get_document", new_callable=AsyncMock, return_value={"posts_count": 5}) as mock_get:
        result = await read_stat_from_firestore(hired_id)
        mock_get.assert_called_once_with("agent_performance", str(hired_id))
        assert result == {"posts_count": 5}


@pytest.mark.asyncio
async def test_rollback_to_sql_stops_firestore_reads(monkeypatch):
    """Simulates operator flipping DATA_ROUTER_MODE back to sql."""
    set_mode(monkeypatch, "sql")
    hired_id = uuid4()
    from services.performance_stat_router import read_stat_from_firestore
    with patch("services.performance_stat_router.get_document", new_callable=AsyncMock) as mock_get:
        result = await read_stat_from_firestore(hired_id)
        mock_get.assert_not_called()
        assert result is None
