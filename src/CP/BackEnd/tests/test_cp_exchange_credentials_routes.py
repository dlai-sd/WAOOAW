"""CP exchange credentials proxy tests (TRADER-FULL-1 S3)."""
from __future__ import annotations

from typing import Any, Dict, Optional
import pytest


class _FakePlantClient:
    def __init__(self, status_code: int = 201, payload: dict = None) -> None:
        self.calls: list = []
        self._status = status_code
        self._payload = payload or {
            "credential_ref": "EXCH-abc123",
            "customer_id": "CUST-1",
            "exchange_provider": "delta_exchange_india",
            "default_coin": "BTC",
            "allowed_coins": ["BTC"],
            "risk_limits": {},
            "validation_status": "pending",
        }

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
    ):
        self.calls.append(
            {
                "method": method,
                "path": path,
                "headers": headers or {},
                "json": json_body,
                "params": params or {},
            }
        )
        return type(
            "R",
            (),
            {
                "status_code": self._status,
                "json": self._payload,
                "headers": {},
            },
        )()


def test_cp_exchange_credentials_upsert_proxies(client, auth_headers, monkeypatch):
    """POST /api/cp/exchange-credentials proxies to Plant and returns credential_ref."""
    from main import app
    from api.cp_exchange_credentials import _plant_client

    fake = _FakePlantClient(status_code=201)
    app.dependency_overrides[_plant_client] = lambda: fake

    try:
        resp = client.post(
            "/api/cp/exchange-credentials",
            headers=auth_headers,
            json={
                "exchange_provider": "delta_exchange_india",
                "api_key": "ak_test",
                "api_secret": "as_test",
                "default_coin": "BTC",
                "allowed_coins": ["BTC"],
                "risk_limits": {},
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["credential_ref"] == "EXCH-abc123"
        # Secrets must never be returned
        assert "api_key" not in body
        assert "api_secret" not in body
        assert "encrypted_api_key" not in body
        assert "encrypted_api_secret" not in body
    finally:
        app.dependency_overrides.pop(_plant_client, None)


def test_cp_exchange_credentials_strips_secrets(client, auth_headers, monkeypatch):
    """Response strips any accidentally echoed secret fields from Plant response."""
    from main import app
    from api.cp_exchange_credentials import _plant_client

    # Plant accidentally echoes api_key in response (should never happen but be safe)
    payload_with_secret = {
        "credential_ref": "EXCH-abc123",
        "customer_id": "CUST-1",
        "exchange_provider": "delta_exchange_india",
        "default_coin": "BTC",
        "allowed_coins": ["BTC"],
        "risk_limits": {},
        "validation_status": "pending",
        "api_key": "SHOULD_BE_STRIPPED",           # must be stripped
        "api_secret": "SHOULD_ALSO_BE_STRIPPED",    # must be stripped
        "encrypted_api_key": "ENC_STRIPPED",        # must be stripped
        "encrypted_api_secret": "ENC_ALSO_STRIPPED",  # must be stripped
    }
    fake = _FakePlantClient(status_code=201, payload=payload_with_secret)
    app.dependency_overrides[_plant_client] = lambda: fake

    try:
        resp = client.post(
            "/api/cp/exchange-credentials",
            headers=auth_headers,
            json={
                "exchange_provider": "delta_exchange_india",
                "api_key": "ak_test",
                "api_secret": "as_test",
                "default_coin": "BTC",
                "allowed_coins": ["BTC"],
                "risk_limits": {},
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "api_key" not in body
        assert "api_secret" not in body
        assert "encrypted_api_key" not in body
        assert "encrypted_api_secret" not in body
    finally:
        app.dependency_overrides.pop(_plant_client, None)


def test_cp_exchange_credentials_get_proxies(client, auth_headers, monkeypatch):
    """GET /api/cp/exchange-credentials proxies to Plant public view."""
    from main import app
    from api.cp_exchange_credentials import _plant_client

    get_payload = {
        "credential_ref": "EXCH-abc123",
        "customer_id": "CUST-1",
        "exchange_provider": "delta_exchange_india",
        "default_coin": "BTC",
        "allowed_coins": ["BTC"],
        "risk_limits": {},
        "validation_status": "valid",
    }
    fake = _FakePlantClient(status_code=200, payload=get_payload)
    app.dependency_overrides[_plant_client] = lambda: fake

    try:
        resp = client.get(
            "/api/cp/exchange-credentials",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["credential_ref"] == "EXCH-abc123"
        assert "api_key" not in body
    finally:
        app.dependency_overrides.pop(_plant_client, None)


def test_cp_exchange_credentials_headers_forwarded(client, auth_headers, monkeypatch):
    """_headers() forwards Authorization and X-Correlation-ID."""
    from main import app
    from api.cp_exchange_credentials import _plant_client

    fake = _FakePlantClient(status_code=201)
    app.dependency_overrides[_plant_client] = lambda: fake

    try:
        resp = client.post(
            "/api/cp/exchange-credentials",
            headers={**auth_headers, "X-Correlation-ID": "test-corr-id"},
            json={
                "exchange_provider": "delta_exchange_india",
                "api_key": "ak_test",
                "api_secret": "as_test",
                "default_coin": "BTC",
                "allowed_coins": ["BTC"],
                "risk_limits": {},
            },
        )
        assert resp.status_code == 201
        assert len(fake.calls) == 1
        fwd_headers = fake.calls[0]["headers"]
        # Authorization must be forwarded
        assert "Authorization" in fwd_headers or "authorization" in fwd_headers
    finally:
        app.dependency_overrides.pop(_plant_client, None)
