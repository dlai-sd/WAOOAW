"""Audit FastAPI dependency — C1 (NFR It-2 reusable interface).

Provides a one-line-per-route audit logger that any route can inject via
``Depends(get_audit_logger)``.

Problem solved:
    Previously, firing an audit event required: importing AuditClient,
    constructing it with base_url + key, calling .log(), and wrapping in
    fire_and_forget_audit(). Four steps — so routes skipped it entirely.

Solution:
    Add ``audit: AuditLogger = Depends(get_audit_logger)`` to a route, then:
    ``await audit.log("cp_registration", "otp_sent", "success", email=email)``

The AuditLogger:
- Pulls AuditClient config from application settings automatically.
- Reads correlation_id and ip_address from the incoming Request.
- All log calls are fire-and-forget — they never block the response.
- Any error inside AuditClient.log() is silently swallowed (see audit_client.py).

Usage::

    from services.audit_dependency import AuditLogger, get_audit_logger

    @router.post("/register")
    async def register(
        body: RegistrationRequest,
        audit: AuditLogger = Depends(get_audit_logger),
    ):
        result = await do_registration(body)
        await audit.log(
            screen="cp_registration",
            action="registration_complete",
            outcome="success",
            email=body.email,
        )
        return result
"""

from __future__ import annotations

import uuid
from typing import Literal, Optional

from fastapi import Depends, Request

from core.config import Settings, get_settings
from services.audit_client import AuditClient, fire_and_forget_audit

AuditOutcome = Literal["success", "failure"]


class AuditLogger:
    """Thin wrapper around AuditClient that auto-populates request context.

    Instantiated once per request by the ``get_audit_logger`` dependency.
    """

    def __init__(
        self,
        *,
        client: AuditClient,
        request: Request,
    ) -> None:
        self._client = client
        self._request = request

    async def log(
        self,
        screen: str,
        action: str,
        outcome: AuditOutcome,
        *,
        user_id: Optional[uuid.UUID] = None,
        email: Optional[str] = None,
        detail: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Fire-and-forget audit event. Never blocks the caller.

        Args:
            screen:   UI screen or service name, e.g. "cp_registration".
            action:   What happened, e.g. "otp_sent", "login_success".
            outcome:  "success" or "failure".
            user_id:  Customer UUID if authenticated.
            email:    Customer email (will be masked in logs by AuditClient).
            detail:   Short human-readable description of the event.
            metadata: Arbitrary key-value pairs for additional context.
        """
        correlation_id: Optional[str] = self._request.headers.get(
            "X-Correlation-ID"
        ) or self._request.headers.get("x-correlation-id")

        client_ip: Optional[str] = None
        forwarded_for = self._request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif self._request.client:
            client_ip = self._request.client.host

        user_agent: Optional[str] = self._request.headers.get("user-agent")

        fire_and_forget_audit(
            self._client.log(
                screen=screen,
                action=action,
                outcome=outcome,
                user_id=user_id,
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                detail=detail,
                metadata=metadata,
                correlation_id=correlation_id,
            )
        )


def get_audit_logger(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuditLogger:
    """FastAPI dependency — inject into any route that needs to emit audit events.

    Example::

        @router.post("/login")
        async def login(audit: AuditLogger = Depends(get_audit_logger)):
            ...
            await audit.log("cp_login", "login_success", "success", email=email)
    """
    client = AuditClient(
        base_url=settings.PLANT_API_URL,
        key=settings.AUDIT_SERVICE_KEY,
    )
    return AuditLogger(client=client, request=request)
