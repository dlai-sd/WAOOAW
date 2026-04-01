from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from services.content_analytics import ContentRecommendation


@pytest.fixture
async def client():
    from api.v1.content_analytics import router
    from core.database import get_read_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _fake_read_db():
        yield object()

    app.dependency_overrides[get_read_db_session] = _fake_read_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
async def test_content_analytics_returns_populated_recommendation(client, monkeypatch):
    async def _fake_get_content_recommendations(hired_instance_id: str, db, lookback_days: int = 30):
        assert hired_instance_id == "HIRED-1"
        return ContentRecommendation(
            top_dimensions=["education", "shorts"],
            best_posting_hours=[9, 14, 18],
            avg_engagement_rate=0.042,
            total_posts_analyzed=12,
            recommendation_text="Double down on education-first shorts.",
        )

    monkeypatch.setattr(
        "api.v1.content_analytics.get_content_recommendations",
        _fake_get_content_recommendations,
    )

    response = await client.get("/api/v1/hired-agents/HIRED-1/content-recommendations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_dimensions"] == ["education", "shorts"]
    assert payload["best_posting_hours"] == [9, 14, 18]
    assert payload["recommendation_text"] == "Double down on education-first shorts."


@pytest.mark.asyncio
async def test_content_analytics_returns_empty_recommendation(client, monkeypatch):
    async def _fake_get_content_recommendations(hired_instance_id: str, db, lookback_days: int = 30):
        return ContentRecommendation(
            total_posts_analyzed=0,
            recommendation_text="No historical data yet — use default content strategy.",
        )

    monkeypatch.setattr(
        "api.v1.content_analytics.get_content_recommendations",
        _fake_get_content_recommendations,
    )

    response = await client.get("/api/v1/hired-agents/HIRED-2/content-recommendations")

    assert response.status_code == 200
    assert response.json()["total_posts_analyzed"] == 0
