"""PP Audit FastAPI dependency — PP-N4 (NFR It-2 reusable interface for PP).

Provides a one-line-per-route audit logger that any PP route can inject via
``Depends(get_audit_logger)``.

Usage::

    from services.audit_dependency import AuditLogger, get_audit_logger

    @router.post("/agents")
    async def create_agent(
        body: AgentCreate,
        audit: AuditLogger = Depends(get_audit_logger),
    ):
        agent = await do_create(body)
        await audit.log(
            screen="pp_agents",
            action="agent_created",
            outcome="success",
            detail=f"Agent {agent.get('id')} created",
        )
        return agent
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
            screen:   Service/screen name, e.g. "pp_agents", "pp_approvals".
            action:   What happened, e.g. "agent_created", "approval_minted".
            outcome:  "success" or "failure".
            user_id:  Admin user UUID if authenticated.
            email:    User email (masked in logs by AuditClient).
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
    """FastAPI dependency — inject into any PP route that needs to emit audit events.

    Example::

        @router.post("/agents")
        async def create_agent(audit: AuditLogger = Depends(get_audit_logger)):
            ...
            await audit.log("pp_agents", "agent_created", "success")
    """
    client = AuditClient(
        base_url=settings.plant_base_url,
        key=settings.AUDIT_SERVICE_KEY,
    )
    return AuditLogger(client=client, request=request)
