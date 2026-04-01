from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI

from core.database import get_read_db_session
from services.content_analytics import ContentRecommendation


@pytest.fixture
async def client():
    from api.v1.content_analytics import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _override_read():
        yield AsyncMock()

    app.dependency_overrides[get_read_db_session] = _override_read

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_content_recommendations_returns_populated_payload(client):
    recommendation = ContentRecommendation(
        top_dimensions=["tutorial", "behind_the_scenes"],
        best_posting_hours=[9, 14, 18],
        avg_engagement_rate=0.042,
        total_posts_analyzed=12,
        recommendation_text="Focus on tutorials in the afternoon.",
    )

    with patch(
        "api.v1.content_analytics.get_content_recommendations",
        AsyncMock(return_value=recommendation),
    ):
        response = await client.get("/api/v1/hired-agents/HIRED-123/content-recommendations")

    assert response.status_code == 200
    data = response.json()
    assert data["top_dimensions"] == ["tutorial", "behind_the_scenes"]
    assert data["best_posting_hours"] == [9, 14, 18]
    assert data["recommendation_text"] == "Focus on tutorials in the afternoon."


@pytest.mark.asyncio
async def test_content_recommendations_returns_empty_payload(client):
    recommendation = ContentRecommendation(
        total_posts_analyzed=0,
        recommendation_text="No historical data yet — use default content strategy.",
    )

    with patch(
        "api.v1.content_analytics.get_content_recommendations",
        AsyncMock(return_value=recommendation),
    ):
        response = await client.get("/api/v1/hired-agents/HIRED-456/content-recommendations")

    assert response.status_code == 200
    assert response.json()["total_posts_analyzed"] == 0
