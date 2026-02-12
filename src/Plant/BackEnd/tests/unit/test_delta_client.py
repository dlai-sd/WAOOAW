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


@pytest.mark.asyncio
async def test_delta_client_handles_invalid_json_response():
    """Test error handling when response is not valid JSON."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=0,
    )

    with pytest.raises(DeltaExchangeError) as exc:
        await client.place_order({"symbol": "ETH"}, correlation_id="corr-3")

    assert "not valid JSON" in str(exc.value)
    assert exc.value.correlation_id == "corr-3"


@pytest.mark.asyncio
async def test_delta_client_handles_non_dict_json_response():
    """Test error handling when response JSON is not a dict."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["list", "not", "dict"])

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=0,
    )

    with pytest.raises(DeltaExchangeError) as exc:
        await client.place_order({"symbol": "SOL"}, correlation_id="corr-4")

    assert "must be an object" in str(exc.value)


@pytest.mark.asyncio
async def test_delta_client_retries_on_network_errors():
    """Test retry logic on transient network errors."""
    attempt_count = {"count": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        attempt_count["count"] += 1
        if attempt_count["count"] < 2:
            raise httpx.ConnectError("Connection failed")
        return httpx.Response(200, json={"order_id": "12345"})

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=2,
    )

    resp = await client.place_order({"symbol": "BTC"}, correlation_id="corr-5")
    assert resp["order_id"] == "12345"
    assert attempt_count["count"] == 2


@pytest.mark.asyncio
async def test_delta_client_fails_after_max_retries():
    """Test that client fails after exhausting max retries."""
    attempt_count = {"count": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        attempt_count["count"] += 1
        raise httpx.ConnectError("Connection failed")

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=2,
    )

    with pytest.raises(DeltaExchangeError) as exc:
        await client.place_order({"symbol": "BTC"}, correlation_id="corr-6")

    # Should have attempted 1 initial + 2 retries = 3 total
    assert attempt_count["count"] == 3
    assert "request error" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_delta_client_handles_authentication_errors():
    """Test handling of authentication-related errors (401, 403)."""
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid API key"})

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="invalid-key", api_secret="invalid-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
        max_retries=0,
    )

    with pytest.raises(DeltaExchangeError) as exc:
        await client.place_order({"symbol": "BTC"}, correlation_id="corr-7")

    assert exc.value.status_code == 401
    assert "request failed" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_delta_client_close_position_method():
    """Test close_position method uses correct endpoint."""
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"position_closed": True})

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
    )

    resp = await client.close_position({"coin": "BTC"}, correlation_id="corr-8")
    assert resp["position_closed"] is True
    assert captured["url"].endswith(DeltaExchangeClient.CLOSE_POSITION_PATH)
    assert captured["body"] == {"coin": "BTC"}


@pytest.mark.asyncio
async def test_delta_client_signature_changes_with_body():
    """Test that signature changes when request body changes."""
    signatures = []

    async def handler(request: httpx.Request) -> httpx.Response:
        signatures.append(request.headers.get("x-signature"))
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)

    creds = DeltaCredentials(api_key="test-key", api_secret="test-secret")
    client = DeltaExchangeClient(
        base_url="https://example.test",
        credentials=creds,
        transport=transport,
    )

    await client.place_order({"symbol": "BTC", "quantity": 1}, correlation_id="corr-9")
    await client.place_order({"symbol": "ETH", "quantity": 2}, correlation_id="corr-10")

    # Signatures should be different for different request bodies
    assert len(signatures) == 2
    assert signatures[0] != signatures[1]
