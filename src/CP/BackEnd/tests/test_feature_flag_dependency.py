"""Tests for api/feature_flag_dependency.py (C7 — NFR It-7).

Covers all branches of the require_flag() dependency factory:
- PLANT_GATEWAY_URL not set → uses default
- Plant returns 200 enabled=True → returns True
- Plant returns 200 enabled=False + raise_if_off=True → HTTP 404
- Plant returns 200 enabled=False + raise_if_off=False → returns False
- Plant returns 404 → uses default
- Plant returns unexpected status → uses default
- ServiceUnavailableError → uses default
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi import Request as FastAPIRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(env: str = "test") -> FastAPIRequest:
    """Build a minimal Starlette Request-like object for the dependency."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }
    return FastAPIRequest(scope)


def _make_plant_response(status_code: int, body: dict | str) -> MagicMock:
    from services.plant_gateway_client import PlantGatewayResponse
    return PlantGatewayResponse(
        status_code=status_code,
        json=body,
        headers={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_on_returns_true(monkeypatch):
    """Plant returns enabled=True → dependency resolves to True."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")
    monkeypatch.setenv("CP_REGISTRATION_KEY", "mock-key")

    response = _make_plant_response(200, {"enabled": True, "key": "my_flag"})

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("my_flag")
        result = await dep(_make_request())

    assert result is True


@pytest.mark.asyncio
async def test_flag_off_raise_if_off_raises_404(monkeypatch):
    """Plant returns enabled=False and raise_if_off=True → HTTP 404."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    response = _make_plant_response(200, {"enabled": False, "key": "my_flag"})

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("my_flag", raise_if_off=True)
        with pytest.raises(HTTPException) as exc_info:
            await dep(_make_request())

    assert exc_info.value.status_code == 404
    assert "my_flag" in exc_info.value.detail


@pytest.mark.asyncio
async def test_flag_off_no_raise_returns_false(monkeypatch):
    """Plant returns enabled=False and raise_if_off=False → returns False."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    response = _make_plant_response(200, {"enabled": False, "key": "my_flag"})

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("my_flag", raise_if_off=False)
        result = await dep(_make_request())

    assert result is False


@pytest.mark.asyncio
async def test_plant_404_uses_default_false_raises(monkeypatch):
    """Plant returns 404 (flag unknown) → default=False → HTTP 404 when raise_if_off."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    response = _make_plant_response(404, {"detail": "not found"})

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("unknown_flag")
        with pytest.raises(HTTPException) as exc_info:
            await dep(_make_request())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_plant_404_uses_default_true_passes(monkeypatch):
    """Plant returns 404 + default=True → resolves to True (flag on by default)."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    response = _make_plant_response(404, {"detail": "not found"})

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("unknown_flag", default=True)
        result = await dep(_make_request())

    assert result is True


@pytest.mark.asyncio
async def test_plant_unexpected_status_uses_default(monkeypatch):
    """Plant returns 503 (unexpected) → defaults to False → raises 404."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    response = _make_plant_response(503, "unavailable")

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(return_value=response),
    ):
        from api.feature_flag_dependency import require_flag

        dep = require_flag("my_flag")
        with pytest.raises(HTTPException) as exc_info:
            await dep(_make_request())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_service_unavailable_uses_default(monkeypatch):
    """Circuit open / connection error → falls back to default."""
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-mock")

    from services.plant_gateway_client import ServiceUnavailableError

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(side_effect=ServiceUnavailableError("circuit open")),
    ):
        from api.feature_flag_dependency import require_flag

        # default=False → raise_if_off → 404
        dep = require_flag("my_flag")
        with pytest.raises(HTTPException):
            await dep(_make_request())

        # default=True → pass through
        dep_on = require_flag("my_flag", default=True)
        result = await dep_on(_make_request())
        assert result is True


@pytest.mark.asyncio
async def test_no_plant_url_uses_default(monkeypatch):
    """PLANT_GATEWAY_URL not set → uses default without calling Plant."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    with patch(
        "api.feature_flag_dependency.PlantGatewayClient.request_json",
        new=AsyncMock(),
    ) as mock_req:
        from api.feature_flag_dependency import require_flag

        dep = require_flag("my_flag", default=False, raise_if_off=False)
        result = await dep(_make_request())

    assert result is False
    mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_no_plant_url_default_true_passes(monkeypatch):
    """PLANT_GATEWAY_URL not set + default=True → flag treated as on."""
    monkeypatch.delenv("PLANT_GATEWAY_URL", raising=False)

    from api.feature_flag_dependency import require_flag

    dep = require_flag("my_flag", default=True, raise_if_off=True)
    result = await dep(_make_request())
    assert result is True
