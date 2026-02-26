"""AuditClient — CP backend service for writing audit events to Plant Audit API.

Iteration 2, E3-S1 + E3-S2.

Design:
- Wraps POST /api/v1/audit/events on Plant backend.
- All calls are fire-and-forget via asyncio.create_task() — audit never
  blocks the registration (or any other) user flow.
- If the Plant Audit API is unavailable, slow, or returns an error, the
  exception is caught, logged as a warning, and swallowed.
- Timeout: 2 seconds per call.

Usage:
    from services.audit_client import AuditClient, fire_and_forget_audit

    client = AuditClient(base_url=settings.PLANT_API_URL, key=settings.AUDIT_SERVICE_KEY)

    # Fire-and-forget (does not block caller):
    fire_and_forget_audit(client.log(
        screen="cp_registration",
        action="otp_sent",
        outcome="success",
        email=email,
        correlation_id=correlation_id,
    ))
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Literal, Optional
import uuid

import httpx

logger = logging.getLogger(__name__)

_AUDIT_EVENTS_PATH = "/api/v1/audit/events"
_DEFAULT_TIMEOUT_SECONDS = 2.0

AuditOutcome = Literal["success", "failure"]


class AuditClient:
    """HTTP client for writing audit events to Plant Audit API."""

    def __init__(
        self,
        *,
        base_url: str,
        key: str,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._key = key
        self._timeout = timeout_seconds

    async def log(
        self,
        *,
        screen: str,
        action: str,
        outcome: AuditOutcome,
        user_id: Optional[uuid.UUID] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        detail: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Write a single audit event. Swallows all exceptions."""
        payload: Dict[str, Any] = {
            "screen": screen,
            "action": action,
            "outcome": outcome,
        }
        if user_id is not None:
            payload["user_id"] = str(user_id)
        if email is not None:
            payload["email"] = email
        if ip_address is not None:
            payload["ip_address"] = ip_address
        if user_agent is not None:
            payload["user_agent"] = user_agent
        if detail is not None:
            payload["detail"] = detail
        if metadata is not None:
            payload["metadata"] = metadata
        if correlation_id is not None:
            payload["correlation_id"] = correlation_id

        url = f"{self._base_url}{_AUDIT_EVENTS_PATH}"
        headers = {"X-Audit-Service-Key": self._key, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                logger.warning(
                    "audit_client: non-2xx response %s for screen=%s action=%s",
                    resp.status_code,
                    screen,
                    action,
                )
        except httpx.TimeoutException:
            logger.warning(
                "audit_client: timeout writing screen=%s action=%s", screen, action
            )
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "audit_client: error writing screen=%s action=%s",
                screen,
                action,
                exc_info=True,
            )


def fire_and_forget_audit(coro: Any) -> None:  # type: ignore[type-arg]
    """Schedule an audit coroutine as a background asyncio task.

    E3-S2: The audit call is completely non-blocking — the caller never awaits
    it and any exception inside is swallowed by the AuditClient.log() wrapper.

    Args:
        coro: Coroutine returned by AuditClient.log(...)
    """
    asyncio.create_task(coro)
