from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.brand_voice import BrandVoiceModel
from services.brand_voice_service import get_brand_voice, upsert_brand_voice


@pytest.mark.unit
def test_brand_voice_model_instantiation_generates_defaults():
    voice = BrandVoiceModel(
        customer_id="c1",
        tone_keywords=["professional"],
    )

    assert voice.customer_id == "c1"
    assert voice.tone_keywords == ["professional"]
    assert voice.vocabulary_preferences == []
    assert uuid.UUID(voice.id)
    assert voice.created_at is not None
    assert voice.updated_at is not None


@pytest.mark.asyncio
async def test_get_brand_voice_returns_existing_model():
    voice = BrandVoiceModel(customer_id="c1", tone_keywords=["professional"])
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = voice
    db.execute.return_value = result

    found = await get_brand_voice("c1", db)

    assert found is voice
    assert found.customer_id == "c1"


@pytest.mark.asyncio
async def test_upsert_brand_voice_creates_then_updates_existing_model():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    first_result = MagicMock()
    first_result.scalar_one_or_none.return_value = None
    existing = BrandVoiceModel(customer_id="c1", tone_keywords=["formal"])
    second_result = MagicMock()
    second_result.scalar_one_or_none.return_value = existing
    db.execute.side_effect = [first_result, second_result]

    created = await upsert_brand_voice("c1", {"tone_keywords": ["casual"]}, db)
    updated = await upsert_brand_voice(
        "c1",
        {"tone_keywords": ["friendly"], "voice_description": "Warm and simple"},
        db,
    )

    db.add.assert_called_once()
    assert created.customer_id == "c1"
    assert created.tone_keywords == ["casual"]
    assert updated.tone_keywords == ["friendly"]
    assert updated.voice_description == "Warm and simple"
