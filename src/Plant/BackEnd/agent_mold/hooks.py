"""Hook bus and enforcement hooks.

Chunk B goal:
- Provide a non-bypassable interception mechanism that can be wired into:
  - Plant Gateway (enforcement proxy)
  - Plant Backend agent execution endpoints
  - AI Explorer (LLM front door)

The bus is intentionally in-process for now. Later phases can move the same
concepts behind a message bus/queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4
from typing import Any, Dict, List, Optional, Protocol


class HookStage(str, Enum):
    SESSION_START = "session_start"
    PRE_SKILL = "pre_skill"
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    POST_SKILL = "post_skill"
    SESSION_END = "session_end"


@dataclass(frozen=True)
class HookEvent:
    stage: HookStage
    correlation_id: str
    agent_id: str
    customer_id: Optional[str] = None
    purpose: Optional[str] = None
    action: Optional[str] = None
    payload: Dict[str, Any] = None  # type: ignore[assignment]
    created_at: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.payload is None:
            object.__setattr__(self, "payload", {})
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.utcnow())


@dataclass(frozen=True)
class HookDecision:
    allowed: bool
    reason: str
    decision_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class Hook(Protocol):
    def handle(self, event: HookEvent) -> Optional[HookDecision]:
        """Return a decision to allow/deny, or None to abstain."""


class HookBus:
    def __init__(self) -> None:
        self._hooks: Dict[HookStage, List[Hook]] = {stage: [] for stage in HookStage}

    def register(self, stage: HookStage, hook: Hook) -> None:
        self._hooks[stage].append(hook)

    def emit(self, event: HookEvent) -> HookDecision:
        """Run hooks in order; first deny stops the chain."""

        for hook in self._hooks.get(event.stage, []):
            decision = hook.handle(event)
            if decision is None:
                continue
            if not decision.allowed:
                if decision.decision_id:
                    return decision
                return HookDecision(
                    allowed=False,
                    reason=decision.reason,
                    decision_id=str(uuid4()),
                    details=decision.details,
                )

        return HookDecision(allowed=True, reason="allowed", decision_id=str(uuid4()))


class ApprovalRequiredHook:
    """Enforce that external publish/send actions require an approval_id.

    This corresponds to the design principle in Base Agent Anatomy:
    - External communication without approval_granted flag → instant block

    For Chunk B, we treat `approval_id` as the canonical signal.
    """

    def __init__(self, *, actions_requiring_approval: Optional[List[str]] = None):
        self._actions_requiring_approval = actions_requiring_approval or [
            "publish",
            "send",
            "post",
        ]

    def handle(self, event: HookEvent) -> Optional[HookDecision]:
        if event.stage != HookStage.PRE_TOOL_USE:
            return None

        if not event.action:
            return None

        action_lower = event.action.lower()
        if action_lower not in self._actions_requiring_approval:
            return None

        approval_id = event.payload.get("approval_id")
        if approval_id:
            return HookDecision(allowed=True, reason="approval_present")

        return HookDecision(
            allowed=False,
            reason="approval_required",
            details={
                "action": event.action,
                "message": "External action requires customer approval_id",
            },
        )
