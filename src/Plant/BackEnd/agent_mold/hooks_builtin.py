# src/Plant/BackEnd/agent_mold/hooks_builtin.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from agent_mold.hooks import HookDecision, HookEvent, HookStage

logger = logging.getLogger(__name__)

EXPIRY_WARNING_DAYS = 7


class CredentialExpiryHook:
    """PRE_PUMP hook: warns (logs + event payload) when a connector credential
    expires within EXPIRY_WARNING_DAYS days.

    Does NOT halt execution — it emits a warning so the platform can notify
    the customer asynchronously. Resolves Gap G11 from AGENT-CONSTRUCT-DESIGN.md.

    HookEvent.payload expected keys:
      connector_expires_at: ISO-8601 datetime string (optional — if absent, hook skips)
    """

    def handle(self, event: HookEvent) -> HookDecision:
        expires_at_str: str | None = event.payload.get("connector_expires_at")
        if not expires_at_str:
            return HookDecision(proceed=True, reason="no_expiry_field")

        try:
            expires_at = datetime.fromisoformat(expires_at_str).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return HookDecision(proceed=True, reason="invalid_expiry_format")

        days_left = (expires_at - datetime.now(timezone.utc)).days
        if days_left <= EXPIRY_WARNING_DAYS:
            logger.warning(
                "credential_expiring_soon",
                extra={
                    "hired_agent_id": event.hired_agent_id,
                    "agent_type": event.agent_type,
                    "days_left": days_left,
                    "expires_at": expires_at_str,
                    # Note: PIIMaskingFilter is active — no email/phone here
                },
            )
            # Return proceed=True BUT flag the warning in metadata
            return HookDecision(
                proceed=True,
                reason="credential_expiring_soon",
                metadata={"days_left": days_left},
            )

        return HookDecision(proceed=True, reason="credential_ok")
