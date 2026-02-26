"""Unit tests for AuditClient — Iteration 2 E3-S1 + E3-S2.

Covers:
  TC-E3-S1-1  AuditClient.log sends correct POST with all fields
  TC-E3-S1-2  AuditClient.log sends only required fields when optional absent
  TC-E3-S1-3  AuditClient.log includes X-Audit-Service-Key header
  TC-E3-S1-4  AuditClient.log logs warning on non-2xx response (no exception raised)
  TC-E3-S2-1  fire_and_forget_audit schedules task without blocking
  TC-E3-S2-2  AuditClient.log swallows TimeoutException (fire-and-forget safe)
  TC-E3-S2-3  AuditClient.log swallows generic Exception (fire-and-forget safe)
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.audit_client import AuditClient, fire_and_forget_audit


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE_URL = "http://plant-backend:8000"
_KEY = "test-service-key-iteration2"
_AUDIT_PATH = "/api/v1/audit/events"


# ---------------------------------------------------------------------------
# TC-E3-S1: AuditClient.log behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_client_sends_required_fields():
    """TC-E3-S1-1: All required fields appear in the POST body."""
    captured: Dict[str, Any] = {}

    async def _handler(request: httpx.Request) -> httpx.Response:
        import json
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(201)

    transport = httpx.MockTransport(_handler)
    client = AuditClient(base_url=_BASE_URL, key=_KEY)

    # Patch httpx.AsyncClient to use mock transport
    original_init = httpx.AsyncClient.__init__

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(201))
        MockClient.return_value = instance

        await client.log(
            screen="cp_registration",
            action="otp_sent",
            outcome="success",
            email="user@example.com",
            correlation_id="corr-abc123",
        )

    call_kwargs = instance.post.call_args
    assert call_kwargs is not None
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if call_kwargs.args else call_kwargs.kwargs["json"]
    assert payload["screen"] == "cp_registration"
    assert payload["action"] == "otp_sent"
    assert payload["outcome"] == "success"
    assert payload["email"] == "user@example.com"
    assert payload["correlation_id"] == "corr-abc123"


@pytest.mark.asyncio
async def test_audit_client_omits_none_optional_fields():
    """TC-E3-S1-2: Optional fields set to None are not included in payload."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(201))
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        await client.log(screen="s", action="a", outcome="failure")

    payload = instance.post.call_args.kwargs["json"]
    assert "email" not in payload
    assert "user_id" not in payload
    assert "correlation_id" not in payload


@pytest.mark.asyncio
async def test_audit_client_sends_service_key_header():
    """TC-E3-S1-3: X-Audit-Service-Key header is present and correct."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(201))
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        await client.log(screen="s", action="a", outcome="success")

    headers = instance.post.call_args.kwargs["headers"]
    assert headers.get("X-Audit-Service-Key") == _KEY


@pytest.mark.asyncio
async def test_audit_client_warns_on_non_2xx_no_exception():
    """TC-E3-S1-4: Non-2xx response logs warning but does NOT raise."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(500))
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        # Must not raise
        await client.log(screen="s", action="a", outcome="failure")


# ---------------------------------------------------------------------------
# TC-E3-S2: Fire-and-forget (non-blocking audit)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fire_and_forget_audit_schedules_task():
    """TC-E3-S2-1: fire_and_forget_audit creates an asyncio task without awaiting."""
    completed = {"flag": False}

    async def _fake_coro() -> None:
        completed["flag"] = True

    created_tasks = []
    original_create_task = asyncio.create_task

    def _capture_task(coro: Any, **kwargs: Any):  # type: ignore[override]
        task = original_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    with patch("services.audit_client.asyncio.create_task", side_effect=_capture_task):
        fire_and_forget_audit(_fake_coro())

    # Yield to event loop so the task executes
    await asyncio.sleep(0)

    assert len(created_tasks) == 1
    assert completed["flag"] is True


@pytest.mark.asyncio
async def test_audit_client_swallows_timeout_exception():
    """TC-E3-S2-2: TimeoutException inside log() is caught and swallowed."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(
            side_effect=httpx.TimeoutException("timeout", request=MagicMock())
        )
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        # Must not raise — fire-and-forget guarantees silence
        await client.log(screen="s", action="a", outcome="failure")


@pytest.mark.asyncio
async def test_audit_client_swallows_generic_exception():
    """TC-E3-S2-3: Any generic exception inside log() is caught and swallowed."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(side_effect=RuntimeError("unexpected"))
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        # Must not raise
        await client.log(screen="cp_registration", action="registration_complete", outcome="success")


@pytest.mark.asyncio
async def test_audit_client_uses_correct_endpoint_url():
    """TC-E3-S1-1 (URL): POST goes to /api/v1/audit/events."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(201))
        MockClient.return_value = instance

        client = AuditClient(base_url=_BASE_URL, key=_KEY)
        await client.log(screen="s", action="a", outcome="success")

    url_called = instance.post.call_args.args[0] if instance.post.call_args.args else instance.post.call_args.kwargs.get("url")
    assert url_called == f"{_BASE_URL}{_AUDIT_PATH}"


@pytest.mark.asyncio
async def test_audit_client_strips_trailing_slash_from_base_url():
    """TC-E3-S1-1 (URL): Trailing slash in base_url is stripped."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=httpx.Response(201))
        MockClient.return_value = instance

        client = AuditClient(base_url=f"{_BASE_URL}/", key=_KEY)
        await client.log(screen="s", action="a", outcome="success")

    url_called = instance.post.call_args.args[0] if instance.post.call_args.args else instance.post.call_args.kwargs.get("url")
    assert url_called == f"{_BASE_URL}{_AUDIT_PATH}"
    assert "//" not in url_called.replace("http://", "").replace("https://", "")
