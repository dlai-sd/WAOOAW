import json

import httpx
import pytest

from integrations.delta_exchange.client import (
    DeltaCredentials,
    DeltaExchangeClient,
    DeltaExchangeError,
)


@pytest.mark.asyncio
async def test_delta_client_enforces_allowlist():
    creds = DeltaCredentials(api_key="k", api_secret="s")
    client = DeltaExchangeClient(base_url="https://example.test", credentials=creds)

    with pytest.raises(DeltaExchangeError) as exc:
        await client._request(method="POST", path="/not-allowed", json_body={})  # type: ignore[attr-defined]

    assert "allowlisted" in str(exc.value)


@pytest.mark.asyncio
async def test_delta_client_sends_signature_and_key_headers():
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
    )

    resp = await client.place_order({"symbol": "BTC"}, correlation_id="corr-1")
    assert resp["ok"] is True

    assert captured["url"].endswith(DeltaExchangeClient.PLACE_ORDER_PATH)
    assert captured["headers"].get("x-api-key") == "test-key"
    assert captured["headers"].get("x-signature")
    assert captured["headers"].get("x-timestamp")
    assert captured["headers"].get("x-correlation-id") == "corr-1"

    body = json.loads(captured["body"])
    assert body == {"symbol": "BTC"}


@pytest.mark.asyncio
async def test_delta_client_redacts_secrets_from_error_messages():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="bad key=test-key secret=test-secret")

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=0,
    )

    with pytest.raises(DeltaExchangeError) as exc:
        await client.place_order({"a": 1}, correlation_id="corr-2")

    message = str(exc.value)
    assert "test-key" not in message
    assert "test-secret" not in message
