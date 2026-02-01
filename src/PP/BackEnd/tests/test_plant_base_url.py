from __future__ import annotations

import pytest

from clients.plant_client import PlantAPIClient
from core.config import settings


@pytest.mark.unit
async def test_plant_base_url_prefers_gateway(monkeypatch):
    monkeypatch.setattr(settings, "PLANT_API_URL", "http://localhost:8000", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "http://plant-gateway:8000", raising=False)

    assert settings.plant_base_url == "http://plant-gateway:8000"

    client = PlantAPIClient()
    try:
        assert client.base_url == "http://plant-gateway:8000"
    finally:
        await client.close()


@pytest.mark.unit
async def test_plant_base_url_falls_back_to_api_url(monkeypatch):
    monkeypatch.setattr(settings, "PLANT_API_URL", "http://localhost:8000", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "", raising=False)

    assert settings.plant_base_url == "http://localhost:8000"

    client = PlantAPIClient()
    try:
        assert client.base_url == "http://localhost:8000"
    finally:
        await client.close()
