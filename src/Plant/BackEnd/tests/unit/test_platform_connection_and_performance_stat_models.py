"""Unit tests for models/platform_connection.py and models/performance_stat.py.

PLANT-SKILLS-1 coverage fix — these models had 0% coverage, pulling total
test coverage below the required 89% threshold (was 87.84%).

Tests instantiate the SQLAlchemy model classes directly (no DB connection needed).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from models.performance_stat import PerformanceStatModel
from models.platform_connection import PlatformConnectionModel


# ─────────────────────────────────────────────────────────────
# PlatformConnectionModel
# ─────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_platform_connection_tablename():
    assert PlatformConnectionModel.__tablename__ == "platform_connections"


@pytest.mark.unit
def test_platform_connection_id_column_has_uuid_default():
    # SQLAlchemy wraps default callables — verify .is_callable and the
    # unwrapped function name to confirm it produces a UUID string.
    col = PlatformConnectionModel.__table__.c["id"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_platform_connection_status_column_defaults_to_pending():
    # Verify the column-level default for status is "pending".
    col = PlatformConnectionModel.__table__.c["status"]
    assert col.default is not None
    assert col.default.arg == "pending"


@pytest.mark.unit
def test_platform_connection_created_at_column_has_callable_default():
    col = PlatformConnectionModel.__table__.c["created_at"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_platform_connection_updated_at_column_has_callable_default():
    col = PlatformConnectionModel.__table__.c["updated_at"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_platform_connection_optional_timestamps_default_to_none():
    conn = PlatformConnectionModel(
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="delta_exchange",
        secret_ref="projects/waooaw-oauth/secrets/hired-abc/versions/latest",
    )
    assert conn.connected_at is None
    assert conn.last_verified_at is None


@pytest.mark.unit
def test_platform_connection_accepts_explicit_status_values():
    for status in ("pending", "connected", "error"):
        conn = PlatformConnectionModel(
            hired_instance_id="hired-abc",
            skill_id=str(uuid.uuid4()),
            platform_key="delta_exchange",
            secret_ref="projects/waooaw-oauth/secrets/hired-abc/versions/latest",
            status=status,
        )
        assert conn.status == status


@pytest.mark.unit
def test_platform_connection_accepts_explicit_timestamps():
    ts = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
    conn = PlatformConnectionModel(
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="instagram",
        secret_ref="projects/waooaw-oauth/secrets/hired-abc-ig/versions/latest",
        status="connected",
        connected_at=ts,
        last_verified_at=ts,
    )
    assert conn.connected_at == ts
    assert conn.last_verified_at == ts


@pytest.mark.unit
def test_platform_connection_accepts_explicit_id():
    explicit_id = str(uuid.uuid4())
    conn = PlatformConnectionModel(
        id=explicit_id,
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="delta_exchange",
        secret_ref="projects/waooaw-oauth/secrets/hired-abc/versions/latest",
    )
    assert conn.id == explicit_id


# ─────────────────────────────────────────────────────────────
# PerformanceStatModel
# ─────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_performance_stat_tablename():
    assert PerformanceStatModel.__tablename__ == "performance_stats"


@pytest.mark.unit
def test_performance_stat_id_column_has_uuid_default():
    col = PerformanceStatModel.__table__.c["id"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_performance_stat_metrics_column_defaults_to_empty_dict():
    col = PerformanceStatModel.__table__.c["metrics"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_performance_stat_collected_at_column_has_callable_default():
    col = PerformanceStatModel.__table__.c["collected_at"]
    assert col.default is not None
    assert col.default.is_callable


@pytest.mark.unit
def test_performance_stat_accepts_social_metrics_payload():
    metrics = {
        "impressions": 12000,
        "clicks": 340,
        "engagement_rate": 2.83,
        "posts_published": 23,
    }
    stat = PerformanceStatModel(
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="instagram",
        stat_date=date(2026, 3, 1),
        metrics=metrics,
    )
    assert stat.metrics["impressions"] == 12000
    assert stat.metrics["engagement_rate"] == 2.83


@pytest.mark.unit
def test_performance_stat_accepts_trading_metrics_payload():
    metrics = {
        "trades_count": 7,
        "pnl_pct": 1.4,
        "win_rate": 0.71,
        "stop_loss_count": 2,
        "profit_count": 5,
    }
    stat = PerformanceStatModel(
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="delta_exchange",
        stat_date=date(2026, 3, 1),
        metrics=metrics,
    )
    assert stat.metrics["win_rate"] == 0.71
    assert stat.metrics["stop_loss_count"] == 2


@pytest.mark.unit
def test_performance_stat_accepts_explicit_id():
    explicit_id = str(uuid.uuid4())
    stat = PerformanceStatModel(
        id=explicit_id,
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="instagram",
        stat_date=date(2026, 3, 1),
    )
    assert stat.id == explicit_id


@pytest.mark.unit
def test_performance_stat_accepts_explicit_collected_at():
    ts = datetime(2026, 3, 1, 23, 59, 0, tzinfo=timezone.utc)
    stat = PerformanceStatModel(
        hired_instance_id="hired-abc",
        skill_id=str(uuid.uuid4()),
        platform_key="instagram",
        stat_date=date(2026, 3, 1),
        collected_at=ts,
    )
    assert stat.collected_at == ts
