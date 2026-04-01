from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.performance_stat import PerformanceStatModel
from services.content_analytics import get_content_recommendations


def _make_stat(*, hour: int, impressions: int, engagement_rate: float, posts: int, dimension: str):
    return PerformanceStatModel(
        hired_instance_id="hired-001",
        skill_id=str(uuid.uuid4()),
        platform_key="youtube",
        stat_date=date(2026, 3, 1),
        metrics={
            "impressions": impressions,
            "engagement_rate": engagement_rate,
            "posts_published": posts,
            "dimension": dimension,
        },
        collected_at=datetime(2026, 3, 1, hour, 0, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_content_recommendations_returns_aggregated_data():
    rows = [
        _make_stat(hour=9, impressions=400, engagement_rate=0.04, posts=2, dimension="education"),
        _make_stat(hour=12, impressions=800, engagement_rate=0.08, posts=3, dimension="education"),
        _make_stat(hour=15, impressions=300, engagement_rate=0.03, posts=1, dimension="social proof"),
    ]
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute.return_value = result

    recommendation = await get_content_recommendations("hired-001", db)

    assert recommendation.total_posts_analyzed == 6
    assert recommendation.avg_engagement_rate > 0
    assert recommendation.recommendation_text


@pytest.mark.asyncio
async def test_get_content_recommendations_returns_empty_defaults_when_no_rows():
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result

    recommendation = await get_content_recommendations("hired-001", db)

    assert recommendation.total_posts_analyzed == 0
    assert "No historical data" in recommendation.recommendation_text


@pytest.mark.asyncio
async def test_get_content_recommendations_sorts_best_posting_hours_by_impressions():
    rows = [
        _make_stat(hour=9, impressions=200, engagement_rate=0.04, posts=1, dimension="education"),
        _make_stat(hour=12, impressions=900, engagement_rate=0.08, posts=1, dimension="education"),
        _make_stat(hour=9, impressions=500, engagement_rate=0.05, posts=1, dimension="social proof"),
        _make_stat(hour=15, impressions=300, engagement_rate=0.03, posts=1, dimension="how-to"),
    ]
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute.return_value = result

    recommendation = await get_content_recommendations("hired-001", db)

    assert recommendation.best_posting_hours == [12, 9, 15]


@pytest.mark.asyncio
async def test_get_content_recommendations_ranks_top_dimensions_by_engagement():
    rows = [
        _make_stat(hour=9, impressions=200, engagement_rate=0.08, posts=1, dimension="education"),
        _make_stat(hour=12, impressions=250, engagement_rate=0.07, posts=1, dimension="education"),
        _make_stat(hour=15, impressions=300, engagement_rate=0.04, posts=1, dimension="social proof"),
    ]
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute.return_value = result

    recommendation = await get_content_recommendations("hired-001", db)

    assert recommendation.top_dimensions[0] == "education"
