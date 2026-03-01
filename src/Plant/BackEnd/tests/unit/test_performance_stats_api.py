"""Unit tests for Performance Stats API.

PLANT-SKILLS-1 E4-S2

Covers:
- Router import + prefix/tags
- GET — empty list for unknown hired_instance_id
- GET — returns filtered stats
- POST — 201 upsert; returns correct shape
- POST — upsert with existing row updates metrics
- All routes registered

Run:
    docker-compose -f docker-compose.test.yml run --rm \\
      --entrypoint "python -m pytest" plant-backend-test \\
      -q --no-cov tests/unit/test_performance_stats_api.py
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Router import / structural ───────────────────────────────────────────────

def test_import_performance_stats_router():
    """Module must import without error and expose 'router'."""
    from api.v1.performance_stats import router
    assert router is not None


def test_router_prefix():
    from api.v1.performance_stats import router
    assert router.prefix == "/v1/hired-agents"


def test_router_tags():
    from api.v1.performance_stats import router
    assert "performance-stats" in router.tags


def test_all_routes_registered():
    """GET and POST must both be registered."""
    from api.v1.performance_stats import router

    routes = {(frozenset(r.methods), r.path) for r in router.routes}
    assert any("GET" in m and "performance-stats" in p for m, p in routes), \
        "GET performance-stats route not registered"
    assert any("POST" in m and "performance-stats" in p for m, p in routes), \
        "POST performance-stats route not registered"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_stat_model(**overrides):
    """Build a minimal PerformanceStat-like MagicMock."""
    now = datetime.now(timezone.utc)
    stat = MagicMock()
    stat.id = str(uuid.uuid4())
    stat.hired_instance_id = str(uuid.uuid4())
    stat.skill_id = str(uuid.uuid4())
    stat.platform_key = "facebook"
    stat.stat_date = date(2025, 1, 15)
    stat.metrics = {"impressions": 1000, "clicks": 50, "engagement_rate": 0.05}
    stat.collected_at = now
    for k, v in overrides.items():
        setattr(stat, k, v)
    return stat


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def hired_id():
    return str(uuid.uuid4())


@pytest.fixture
def skill_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_read_db():
    db = AsyncMock()
    return db


@pytest.fixture
def mock_write_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


# ── GET /performance-stats ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_performance_stats_empty(hired_id, mock_read_db):
    """GET returns empty list for unknown hired_instance_id (not 404)."""
    from api.v1.performance_stats import get_performance_stats

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_read_db.execute = AsyncMock(return_value=result_mock)

    resp = await get_performance_stats(hired_id, db=mock_read_db)
    assert resp == []


@pytest.mark.asyncio
async def test_get_performance_stats_returns_list(hired_id, mock_read_db):
    """GET returns list of PerformanceStatResponse objects."""
    from api.v1.performance_stats import get_performance_stats

    stat = _make_stat_model(hired_instance_id=hired_id)
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [stat]
    mock_read_db.execute = AsyncMock(return_value=result_mock)

    resp = await get_performance_stats(hired_id, db=mock_read_db)
    assert len(resp) == 1
    assert resp[0].hired_instance_id == stat.hired_instance_id
    assert resp[0].platform_key == stat.platform_key
    assert isinstance(resp[0].metrics, dict)


@pytest.mark.asyncio
async def test_get_performance_stats_with_filters(hired_id, mock_read_db):
    """GET with skill_id + platform_key filters executes (smoke test)."""
    from api.v1.performance_stats import get_performance_stats

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_read_db.execute = AsyncMock(return_value=result_mock)

    skill = str(uuid.uuid4())
    resp = await get_performance_stats(
        hired_id,
        skill_id=skill,
        platform_key="linkedin",
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 31),
        db=mock_read_db,
    )
    assert resp == []
    # Execute must have been called exactly once with the filtered query
    mock_read_db.execute.assert_called_once()


# ── POST /performance-stats ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_performance_stat_201(hired_id, mock_write_db):
    """POST returns a PerformanceStatResponse with correct fields."""
    from api.v1.performance_stats import upsert_performance_stat, UpsertPerformanceStatRequest

    # pg_insert().on_conflict_do_update().returning() path — returns via scalars().first()
    stat = _make_stat_model(
        hired_instance_id=hired_id,
        skill_id=str(uuid.uuid4()),
        platform_key="instagram",
        stat_date=date(2025, 1, 20),
        metrics={"posts_published": 5, "impressions": 2000},
    )
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = stat
    mock_write_db.execute = AsyncMock(return_value=result_mock)

    body = UpsertPerformanceStatRequest(
        skill_id=stat.skill_id,
        platform_key="instagram",
        stat_date=date(2025, 1, 20),
        metrics={"posts_published": 5, "impressions": 2000},
    )

    resp = await upsert_performance_stat(hired_id, body, db=mock_write_db)
    assert resp.hired_instance_id == hired_id
    assert resp.platform_key == "instagram"
    assert isinstance(resp.metrics, dict)
    mock_write_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_performance_stat_updates_metrics(hired_id, mock_write_db):
    """POST upsert updates metrics on duplicate composite key (smoke: execute called)."""
    from api.v1.performance_stats import upsert_performance_stat, UpsertPerformanceStatRequest

    new_metrics = {"posts_published": 10, "impressions": 5000}
    stat = _make_stat_model(
        hired_instance_id=hired_id,
        metrics=new_metrics,
    )
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = stat
    mock_write_db.execute = AsyncMock(return_value=result_mock)

    body = UpsertPerformanceStatRequest(
        skill_id=stat.skill_id,
        platform_key=stat.platform_key,
        stat_date=stat.stat_date,
        metrics=new_metrics,
    )
    resp = await upsert_performance_stat(hired_id, body, db=mock_write_db)
    assert resp.metrics == new_metrics
    mock_write_db.commit.assert_called_once()


# ── Response schema ───────────────────────────────────────────────────────────

def test_to_response_conversion():
    """_to_response maps all fields correctly."""
    from api.v1.performance_stats import _to_response
    stat = _make_stat_model()
    resp = _to_response(stat)
    assert resp.id == stat.id
    assert resp.hired_instance_id == stat.hired_instance_id
    assert resp.skill_id == stat.skill_id
    assert resp.platform_key == stat.platform_key
    assert resp.stat_date == stat.stat_date
    assert resp.metrics == stat.metrics
    assert resp.collected_at == stat.collected_at


def test_to_response_none_metrics_becomes_empty_dict():
    """_to_response returns {} when model.metrics is None."""
    from api.v1.performance_stats import _to_response
    stat = _make_stat_model(metrics=None)
    resp = _to_response(stat)
    assert resp.metrics == {}
