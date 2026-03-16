from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _mock_httpx_get(status_code: int, json_body: dict | list) -> AsyncMock:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.unit
def test_list_catalog_agents_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    payload = [
        {
            "release_id": "CAR-1",
            "id": "AGT-MKT-DMA-001",
            "public_name": "Digital Marketing Agent",
            "lifecycle_state": "live_on_cp",
            "approved_for_new_hire": True,
        }
    ]
    mock_client = _mock_httpx_get(200, payload)

    with patch("api.cp_catalog.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/catalog/agents", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "AGT-MKT-DMA-001"


@pytest.mark.unit
def test_list_catalog_agents_forwards_query_string(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")

    def side_effect_get(url, **kwargs):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_resp.text = "[]"
        assert url.endswith("/api/v1/catalog/agents?industry=marketing")
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=side_effect_get)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_catalog.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/catalog/agents?industry=marketing", headers=auth_headers)

    assert resp.status_code == 200


@pytest.mark.unit
def test_list_catalog_agents_not_found(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_client = _mock_httpx_get(404, {"detail": "not found"})

    with patch("api.cp_catalog.httpx.AsyncClient", return_value=mock_client):
        resp = client.get("/api/cp/catalog/agents", headers=auth_headers)

    assert resp.status_code == 404