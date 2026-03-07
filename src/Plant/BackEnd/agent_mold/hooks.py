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

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4
from typing import Any, Dict, List, Optional, Protocol


class HookStage(str, Enum):
    # --- existing stages (do not remove) ---
    SESSION_START  = "session_start"
    PRE_SKILL      = "pre_skill"
    PRE_TOOL_USE   = "pre_tool_use"
    POST_TOOL_USE  = "post_tool_use"
    POST_SKILL     = "post_skill"
    SESSION_END    = "session_end"
    # --- new stages added by PLANT-MOULD-1 ---
    PRE_PROCESSOR  = "pre_processor"
    POST_PROCESSOR = "post_processor"
    PRE_PUMP       = "pre_pump"
    POST_PUMP      = "post_pump"
    PRE_PUBLISH    = "pre_publish"
    POST_PUBLISH   = "post_publish"


@dataclass(frozen=True)
class HookEvent:
    stage: HookStage
    # Legacy fields (keep for backward compatibility)
    correlation_id: str = ""
    agent_id: str = ""
    customer_id: Optional[str] = None
    purpose: Optional[str] = None
    action: Optional[str] = None
    payload: Dict[str, Any] = None  # type: ignore[assignment]
    created_at: datetime = None  # type: ignore[assignment]
    # New fields added by PLANT-MOULD-1
    hired_agent_id: Optional[str] = None
    agent_type: Optional[str] = None

    def __post_init__(self) -> None:
        if self.payload is None:
            object.__setattr__(self, "payload", {})
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.utcnow())


@dataclass(frozen=True)
class HookDecision:
    reason: str
    allowed: Optional[bool] = None
    decision_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    # `proceed` mirrors `allowed` — new name used by PLANT-MOULD-1 stories.
    proceed: Optional[bool] = None
    # `metadata` carries arbitrary data back to the caller (e.g., days_left for expiry hooks).
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        # Sync allowed ↔ proceed so both names always work.
        if self.allowed is None and self.proceed is not None:
            object.__setattr__(self, "allowed", self.proceed)
        elif self.proceed is None and self.allowed is not None:
            object.__setattr__(self, "proceed", self.allowed)


class Hook(Protocol):
    def handle(self, event: HookEvent) -> Optional[HookDecision]:
        """Return a decision to allow/deny, or None to abstain."""


class HookBus:
    def __init__(self) -> None:
        self._hooks: Dict[HookStage, List[Hook]] = {stage: [] for stage in HookStage}

    def register(self, stage: HookStage, hook: Hook) -> None:
        self._hooks[stage].append(hook)

    def emit(self, stage_or_event: Any, event: Any = None) -> "HookDecision":
        """Run hooks in order; first deny stops the chain.

        Supports two call forms:
          - emit(HookEvent)            — original form; stage comes from event.stage
          - emit(HookStage, event)     — new form; stage is explicit, event can be any object
        """
        if event is None:
            # Called as emit(HookEvent)
            hook_event = stage_or_event
            stage = hook_event.stage
        else:
            # Called as emit(HookStage, event)
            stage = stage_or_event
            hook_event = event

        for hook in self._hooks.get(stage, []):
            # Support Protocol hooks with handle() and callable hooks with __call__()
            if hasattr(hook, "handle"):
                decision = hook.handle(hook_event)
            elif callable(hook):
                decision = hook(hook_event)
            else:
                continue

            if decision is None:
                continue
            # allowed=False or proceed=False means deny (both are synced in __post_init__)
            if decision.allowed is False:
                if decision.decision_id:
                    return decision
                return HookDecision(
                    allowed=False,
                    reason=decision.reason,
                    decision_id=str(uuid4()),
                    details=decision.details,
                )

        return HookDecision(allowed=True, reason="allowed", decision_id=str(uuid4()))


class LifecycleContext:
    """Minimal context passed to every lifecycle event.

    Keeps hooks decoupled from DB session — they receive only what they need.
    Never log ctx.customer_id raw (PIIMaskingFilter handles it at logger level).
    """

    def __init__(
        self,
        hired_instance_id: str,
        agent_type_id: str,
        customer_id: str,
        agent_id: Optional[str] = None,
        deliverable_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.hired_instance_id = hired_instance_id
        self.agent_type_id = agent_type_id
        self.customer_id = customer_id
        self.agent_id = agent_id
        self.deliverable_id = deliverable_id
        self.extra: Dict[str, Any] = extra or {}


class AgentLifecycleHooks(ABC):
    """Base class for agent-type-specific lifecycle event handlers.

    Agent types override only the events they care about.
    All methods are async and non-blocking — a failure must NOT raise to caller.
    Default implementations are silent no-ops (safe to leave unoverridden).
    """

    async def on_hire(self, ctx: LifecycleContext) -> None:
        """Called when a hired agent is finalised (trial or direct hire)."""

    async def on_trial_start(self, ctx: LifecycleContext) -> None:
        """Called when trial_start_at is set on the hired agent."""

    async def on_trial_end(self, ctx: LifecycleContext) -> None:
        """Called when trial period expires (scheduler detects trial_end_date passed)."""

    async def on_trial_day_N(self, ctx: LifecycleContext, day: int) -> None:
        """Called once per trial day N (day=1 on first full day, etc.)."""

    async def on_deliverable_pending_review(self, ctx: LifecycleContext) -> None:
        """Called when a deliverable lands in pending_review status."""

    async def on_deliverable_approved(self, ctx: LifecycleContext) -> None:
        """Called when a customer approves a deliverable.

        For trading agents: triggers DeltaTradeAdapter.execute_approved_order().
        For content agents: triggers Publisher.publish() for approved posts.
        Subclass MUST override if agent has an approval side-effect.
        """

    async def on_deliverable_rejected(self, ctx: LifecycleContext) -> None:
        """Called when a customer rejects a deliverable."""

    async def on_goal_run_start(self, ctx: LifecycleContext) -> None:
        """Called at the start of each goal run (Scheduler fires)."""

    async def on_goal_run_complete(self, ctx: LifecycleContext) -> None:
        """Called when a goal run finishes successfully."""

    async def on_cancel(self, ctx: LifecycleContext) -> None:
        """Called when subscription is cancelled."""

    async def on_quota_exhausted(self, ctx: LifecycleContext) -> None:
        """Called when trial_task_limit is reached."""


class NullLifecycleHooks(AgentLifecycleHooks):
    """No-op lifecycle hooks. Used as default when agent type has no overrides."""


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
            "place_order",
            "close_position",
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
