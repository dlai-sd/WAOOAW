from __future__ import annotations

import base64
import hmac
import time
from hashlib import sha256

import pytest


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


@pytest.mark.unit
async def test_metering_debug_endpoint_404_when_disabled(client, monkeypatch):
    monkeypatch.delenv("ENABLE_METERING_DEBUG", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("METERING_ENVELOPE_SECRET", "secret")

    resp = await client.post(
        "/api/pp/metering-debug/envelope",
        json={"correlation_id": "corr-1", "tokens_in": 1, "tokens_out": 2},
    )
    assert resp.status_code == 404


@pytest.mark.unit
async def test_metering_debug_mints_signature_when_enabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_METERING_DEBUG", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("METERING_ENVELOPE_SECRET", "secret")

    ts = int(time.time())
    payload = {
        "correlation_id": "corr-xyz",
        "tokens_in": 10,
        "tokens_out": 20,
        "model": "gpt-demo",
        "cache_hit": False,
        "cost_usd": 0.1,
        "timestamp": ts,
    }

    resp = await client.post("/api/pp/metering-debug/envelope", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    headers = data["headers"]

    assert headers["X-Metering-Timestamp"] == str(ts)
    assert headers["X-Metering-Tokens-In"] == "10"
    assert headers["X-Metering-Tokens-Out"] == "20"
    assert headers["X-Metering-Model"] == "gpt-demo"
    assert headers["X-Metering-Cache-Hit"] == "0"
    assert headers["X-Metering-Cost-USD"] == "0.100000"

    canonical = f"{ts}|corr-xyz|10|20|gpt-demo|0|0.100000"
    expected = _base64url(hmac.new(b"secret", canonical.encode("utf-8"), sha256).digest())
    assert headers["X-Metering-Signature"] == expected


@pytest.mark.unit
async def test_metering_debug_endpoint_404_in_prod_like_env(client, monkeypatch):
    monkeypatch.setenv("ENABLE_METERING_DEBUG", "true")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("METERING_ENVELOPE_SECRET", "secret")

    resp = await client.post(
        "/api/pp/metering-debug/envelope",
        json={"correlation_id": "corr-1", "tokens_in": 1, "tokens_out": 2},
    )
    assert resp.status_code == 404
