from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from core.security import create_access_token


@pytest.fixture
async def client():
    from api.v1.brand_voice import router
    from core.database import get_db_session, get_read_db_session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    class _FakeSession:
        async def commit(self):
            return None

    async def _fake_read_db():
        yield _FakeSession()

    async def _fake_write_db():
        yield _FakeSession()

    app.dependency_overrides[get_read_db_session] = _fake_read_db
    app.dependency_overrides[get_db_session] = _fake_write_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


def _auth_headers() -> dict[str, str]:
    token = create_access_token(
        {
            "sub": "user-1",
            "user_id": "user-1",
            "email": "user@example.com",
            "token_type": "access",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_brand_voice_get_returns_404_when_missing(client, monkeypatch):
    async def _fake_get_brand_voice(customer_id: str, db):
        assert customer_id == "user-1"
        return None

    monkeypatch.setattr("api.v1.brand_voice.get_brand_voice", _fake_get_brand_voice)

    response = await client.get("/api/v1/brand-voice/me", headers=_auth_headers())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_brand_voice_put_returns_saved_model(client, monkeypatch):
    class _Voice:
        tone_keywords = ["warm", "credible"]
        vocabulary_preferences = ["care", "trust"]
        messaging_patterns = ["hook", "proof"]
        example_phrases = ["We explain every step."]
        voice_description = "Warm and credible."

    async def _fake_upsert_brand_voice(customer_id: str, data: dict, db):
        assert customer_id == "user-1"
        assert data["voice_description"] == "Warm and credible."
        return _Voice()

    monkeypatch.setattr("api.v1.brand_voice.upsert_brand_voice", _fake_upsert_brand_voice)

    response = await client.put(
        "/api/v1/brand-voice/me",
        headers={**_auth_headers(), "Content-Type": "application/json"},
        json={
            "tone_keywords": ["warm", "credible"],
            "vocabulary_preferences": ["care", "trust"],
            "messaging_patterns": ["hook", "proof"],
            "example_phrases": ["We explain every step."],
            "voice_description": "Warm and credible.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tone_keywords"] == ["warm", "credible"]
    assert payload["voice_description"] == "Warm and credible."
