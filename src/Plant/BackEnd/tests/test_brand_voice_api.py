from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI

from core.database import get_db_session, get_read_db_session


@pytest.fixture
async def client():
    from api.v1.brand_voice import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    write_session = AsyncMock()
    write_session.commit = AsyncMock()
    write_session.refresh = AsyncMock()

    async def _override_read():
        yield AsyncMock()

    async def _override_write():
        yield write_session

    app.dependency_overrides[get_read_db_session] = _override_read
    app.dependency_overrides[get_db_session] = _override_write

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_get_brand_voice_returns_404_when_missing(client):
    with (
        patch("api.v1.brand_voice._resolve_customer_id", AsyncMock(return_value="cust-123")),
        patch("api.v1.brand_voice.get_brand_voice", AsyncMock(return_value=None)),
    ):
        response = await client.get(
            "/api/v1/brand-voice/me",
            headers={"Authorization": "Bearer token"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_brand_voice_upserts_and_returns_payload(client):
    model = SimpleNamespace(
        tone_keywords=["confident", "warm"],
        vocabulary_preferences=["growth"],
        messaging_patterns=[],
        example_phrases=["Let us grow together"],
        voice_description="Confident and warm",
    )

    with (
        patch("api.v1.brand_voice._resolve_customer_id", AsyncMock(return_value="cust-123")),
        patch("api.v1.brand_voice.upsert_brand_voice", AsyncMock(return_value=model)),
    ):
        response = await client.put(
            "/api/v1/brand-voice/me",
            headers={"Authorization": "Bearer token"},
            json={
                "tone_keywords": ["confident", "warm"],
                "vocabulary_preferences": ["growth"],
                "messaging_patterns": [],
                "example_phrases": ["Let us grow together"],
                "voice_description": "Confident and warm",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["tone_keywords"] == ["confident", "warm"]
    assert data["voice_description"] == "Confident and warm"
