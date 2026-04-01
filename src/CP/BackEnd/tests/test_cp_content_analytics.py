from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services.plant_gateway_client import PlantGatewayResponse


@pytest.mark.unit
def test_get_content_recommendations_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    response = PlantGatewayResponse(
        status_code=200,
        json={
            "top_dimensions": ["tutorial"],
            "best_posting_hours": [9, 14],
            "avg_engagement_rate": 0.042,
            "total_posts_analyzed": 12,
            "recommendation_text": "Focus on tutorials.",
        },
        headers={},
    )

    mock_client = AsyncMock()
    mock_client.request_json = AsyncMock(return_value=response)

    from main import app
    from api.cp_content_analytics import get_plant_gateway_client

    app.dependency_overrides[get_plant_gateway_client] = lambda: mock_client
    try:
        resp = client.get("/api/cp/content-recommendations/HIRED-001", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["top_dimensions"] == ["tutorial"]


@pytest.mark.unit
def test_get_content_recommendations_upstream_failure_returns_503(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    response = PlantGatewayResponse(status_code=500, json={"detail": "boom"}, headers={})
    mock_client = AsyncMock()
    mock_client.request_json = AsyncMock(return_value=response)

    from main import app
    from api.cp_content_analytics import get_plant_gateway_client

    app.dependency_overrides[get_plant_gateway_client] = lambda: mock_client
    try:
        resp = client.get("/api/cp/content-recommendations/HIRED-001", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 503
