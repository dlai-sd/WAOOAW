from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.plant_gateway_client import PlantGatewayResponse


@pytest.mark.unit
def test_get_brand_voice_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    response = PlantGatewayResponse(
        status_code=200,
        json={
            "tone_keywords": ["confident"],
            "vocabulary_preferences": [],
            "messaging_patterns": [],
            "example_phrases": ["Let us grow together"],
            "voice_description": "Confident and warm",
        },
        headers={},
    )
    mock_client = AsyncMock()
    mock_client.request_json = AsyncMock(return_value=response)

    from main import app
    from api.cp_brand_voice import get_plant_gateway_client

    app.dependency_overrides[get_plant_gateway_client] = lambda: mock_client
    try:
        resp = client.get("/api/cp/brand-voice", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["voice_description"] == "Confident and warm"


@pytest.mark.unit
def test_put_brand_voice_logs_audit(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    response = PlantGatewayResponse(
        status_code=200,
        json={
            "tone_keywords": ["confident"],
            "vocabulary_preferences": [],
            "messaging_patterns": [],
            "example_phrases": ["Let us grow together"],
            "voice_description": "Confident and warm",
        },
        headers={},
    )
    mock_client = AsyncMock()
    mock_client.request_json = AsyncMock(return_value=response)
    audit = SimpleNamespace(log=AsyncMock())

    from main import app
    from api.cp_brand_voice import get_plant_gateway_client
    from services.audit_dependency import get_audit_logger

    app.dependency_overrides[get_plant_gateway_client] = lambda: mock_client
    app.dependency_overrides[get_audit_logger] = lambda: audit
    try:
        resp = client.put(
            "/api/cp/brand-voice",
            headers=auth_headers,
            json={
                "tone_keywords": ["confident"],
                "voice_description": "Confident and warm",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    audit.log.assert_awaited_once()


@pytest.mark.unit
def test_put_brand_voice_upstream_500_returns_503(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    response = PlantGatewayResponse(status_code=500, json={"detail": "boom"}, headers={})
    mock_client = AsyncMock()
    mock_client.request_json = AsyncMock(return_value=response)

    from main import app
    from api.cp_brand_voice import get_plant_gateway_client

    app.dependency_overrides[get_plant_gateway_client] = lambda: mock_client
    try:
        resp = client.put(
            "/api/cp/brand-voice",
            headers=auth_headers,
            json={"voice_description": "Updated voice"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 503
