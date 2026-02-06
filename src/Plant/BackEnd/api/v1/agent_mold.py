"""Agent Mold enforcement endpoints.

Goal 2: Wire the hook bus into a real, callable API surface.

This is intentionally minimal: the Gateway can call these endpoints as an
enforcement proxy, and internal services can share the same policy plane.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Header, Request, Depends
from pydantic import BaseModel, Field

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.reference_agents import get_reference_agent
from agent_mold.spec import AgentSpec, DimensionName
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import SkillExecutionInput, SkillExecutionResult
from core.exceptions import PolicyEnforcementError, UsageLimitError
from services.metering import (
    compute_effective_estimated_cost_usd,
    enforce_trial_and_budget,
    plan_enforces_budget,
    verify_trusted_metering_envelope_headers,
)
from services.policy_denial_audit import (
    PolicyDenialAuditRecord,
    PolicyDenialAuditStore,
    get_policy_denial_audit_store,
)
from services.usage_ledger import FileUsageLedger, InMemoryUsageLedger, UsageLedger
from services.usage_events import (
    FileUsageEventStore,
    InMemoryUsageEventStore,
    UsageEvent,
    UsageEventStore,
    UsageEventType,
)


router = APIRouter(prefix="/agent-mold", tags=["agent-mold"])

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def agent_spec_json_schema() -> Dict[str, Any]:
    """Return the JSON schema for AgentSpec.

    This is intended for out-of-band validation (e.g., Gateway/clients) without
    having to execute a full runtime compile step.
    """

    return AgentSpec.model_json_schema()


@router.get("/schema/agent-spec")
async def get_agent_spec_schema() -> Dict[str, Any]:
    """Expose the AgentSpec JSON schema for external validation tooling."""

    return agent_spec_json_schema()


class ValidateAgentSpecResponse(BaseModel):
    valid: bool = True


@router.post("/spec/validate", response_model=ValidateAgentSpecResponse)
async def validate_agent_spec(_: AgentSpec) -> ValidateAgentSpecResponse:
    """Validate an AgentSpec and return ok.

    Invalid specs will return 422 automatically via FastAPI/Pydantic.
    """

    return ValidateAgentSpecResponse(valid=True)


@lru_cache(maxsize=1)
def default_usage_ledger() -> UsageLedger:
    path = os.getenv("USAGE_LEDGER_STORE_PATH")
    if path:
        return FileUsageLedger(path)
    return InMemoryUsageLedger()


def get_usage_ledger() -> UsageLedger:
    return default_usage_ledger()


@lru_cache(maxsize=1)
def default_usage_event_store() -> UsageEventStore:
    path = os.getenv("USAGE_EVENTS_STORE_PATH")
    if path:
        return FileUsageEventStore(path)
    return InMemoryUsageEventStore()


def get_usage_event_store() -> UsageEventStore:
    return default_usage_event_store()


class ToolUseEnforceRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None
    customer_id: Optional[str] = None
    purpose: Optional[str] = None
    correlation_id: Optional[str] = None


class ToolUseEnforceResponse(BaseModel):
    allowed: bool
    reason: str
    decision_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@router.post("/tool-use", response_model=ToolUseEnforceResponse)
async def enforce_tool_use(
    body: ToolUseEnforceRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> ToolUseEnforceResponse:
    """Evaluate pre-tool-use policy and return allow/deny.

    If denied, raises PolicyEnforcementError (RFC 7807 via exception handler).
    """

    correlation_id = body.correlation_id or x_correlation_id or str(id(request))

    event_payload = dict(body.payload or {})
    if body.approval_id:
        event_payload["approval_id"] = body.approval_id

    decision = default_hook_bus().emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id=correlation_id,
            agent_id=body.agent_id,
            customer_id=body.customer_id,
            purpose=body.purpose,
            action=body.action,
            payload=event_payload,
        )
    )

    if not decision.allowed:
        # Minimal audit signal for now (log-based). Later phases can persist this
        # via the audit service / ledger.
        logger.warning(
            "policy_denied",
            extra={
                "correlation_id": correlation_id,
                "agent_id": body.agent_id,
                "customer_id": body.customer_id,
                "stage": HookStage.PRE_TOOL_USE,
                "action": body.action,
                "reason": decision.reason,
                "details": decision.details,
            },
        )
        details: Dict[str, Any] = dict(decision.details or {})
        if decision.decision_id:
            details["decision_id"] = decision.decision_id

        policy_audit.append(
            PolicyDenialAuditRecord(
                correlation_id=correlation_id,
                decision_id=decision.decision_id,
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                stage=str(HookStage.PRE_TOOL_USE),
                action=body.action,
                reason=decision.reason,
                path=str(request.url.path),
                details=details,
            )
        )

        raise PolicyEnforcementError(
            "Policy denied tool use",
            reason=decision.reason,
            details=details,
        )

    return ToolUseEnforceResponse(
        allowed=True,
        reason=decision.reason,
        decision_id=decision.decision_id,
        details=decision.details,
    )


@lru_cache(maxsize=1)
def _marketing_multichannel_playbook() -> Any:
    path = (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )
    return load_playbook(path)


class ExecuteMarketingMultichannelRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)

    # Metering / trial context
    customer_id: Optional[str] = None
    trial_mode: bool = False
    trial_id: Optional[UUID] = None
    plan_id: Optional[str] = None
    estimated_cost_usd: float = 0.0

    # Metering payload (from AI Explorer / LLM front-door)
    meter_tokens_in: int = 0
    meter_tokens_out: int = 0
    meter_model: Optional[str] = None
    meter_cache_hit: bool = False

    # Enforcement intent: if you intend an external action, it must be declared
    # and will be enforced.
    intent_action: Optional[str] = None
    # Optional shortcut: allow the agent to attempt publish automatically.
    # This is disabled by default and only allowed when the agent's AgentSpec
    # explicitly permits it.
    autopublish: bool = False
    approval_id: Optional[str] = None

    purpose: Optional[str] = None
    correlation_id: Optional[str] = None

    # Skill execution input
    theme: str
    brand_name: str
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None


@router.post(
    "/skills/marketing/multichannel-post-v1/execute",
    response_model=SkillExecutionResult,
)
async def execute_marketing_multichannel_post_v1(
    body: ExecuteMarketingMultichannelRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    ledger: UsageLedger = Depends(get_usage_ledger),
    events: UsageEventStore = Depends(get_usage_event_store),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> SkillExecutionResult:
    """Execute the marketing multichannel playbook.

    Goal 2: make enforcement non-bypassable for real executions.
    - If `intent_action` is provided (e.g. "publish"), it is enforced via hooks.
    """

    correlation_id = body.correlation_id or x_correlation_id or str(id(request))

    metering_verification = verify_trusted_metering_envelope_headers(
        headers=request.headers,
        correlation_id=correlation_id,
    )

    meter_tokens_in = body.meter_tokens_in
    meter_tokens_out = body.meter_tokens_out
    meter_model = body.meter_model
    meter_cache_hit = body.meter_cache_hit
    estimated_cost_usd = body.estimated_cost_usd

    if metering_verification.envelope is not None:
        meter_tokens_in = metering_verification.envelope.tokens_in
        meter_tokens_out = metering_verification.envelope.tokens_out
        meter_model = metering_verification.envelope.model
        meter_cache_hit = metering_verification.envelope.cache_hit
        estimated_cost_usd = metering_verification.envelope.cost_usd

    if (
        metering_verification.enabled
        and body.customer_id
        and plan_enforces_budget(body.plan_id)
        and metering_verification.status != "trusted"
    ):
        reason = "metering_envelope_required"
        if metering_verification.status in {"invalid", "bad_format"}:
            reason = "metering_envelope_invalid"
        elif metering_verification.status == "stale":
            reason = "metering_envelope_expired"

        raise UsageLimitError(
            "Trusted metering envelope required for budget enforcement",
            reason=reason,
            details={
                "customer_id": body.customer_id,
                "plan_id": body.plan_id,
                "metering_status": metering_verification.status,
            },
        )

    effective_estimated_cost_usd = compute_effective_estimated_cost_usd(
        estimated_cost_usd=estimated_cost_usd,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        meter_model=meter_model,
    )

    intent_action = body.intent_action
    if body.autopublish:
        if intent_action and intent_action.lower() != "publish":
            raise PolicyEnforcementError(
                "Autopublish conflicts with intent_action",
                reason="autopublish_conflicts_intent_action",
                details={
                    "intent_action": intent_action,
                },
            )

        # Only allow autopublish for agents whose AgentSpec explicitly enables it.
        ref = get_reference_agent(body.agent_id)
        allowed = False
        if ref is not None:
            skill_dim = ref.spec.dimensions.get(DimensionName.SKILL)
            allowed = bool(skill_dim and skill_dim.config.get("autopublish_allowed") is True)

        if not allowed:
            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=None,
                    agent_id=body.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action="publish",
                    reason="autopublish_not_allowed",
                    path=str(request.url.path),
                    details={"agent_id": body.agent_id},
                )
            )
            raise PolicyEnforcementError(
                "Autopublish not allowed for agent",
                reason="autopublish_not_allowed",
                details={
                    "agent_id": body.agent_id,
                },
            )

        intent_action = "publish"

    enforce_trial_and_budget(
        correlation_id=correlation_id,
        agent_id=body.agent_id,
        customer_id=body.customer_id,
        plan_id=body.plan_id,
        trial_mode=body.trial_mode,
        intent_action=intent_action,
        effective_estimated_cost_usd=effective_estimated_cost_usd,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        purpose=body.purpose,
        ledger=ledger,
        events=events,
    )

    if intent_action:
        event_payload: Dict[str, Any] = {}
        if body.approval_id:
            event_payload["approval_id"] = body.approval_id
        if body.autopublish:
            event_payload["autopublish"] = True

        decision = default_hook_bus().emit(
            HookEvent(
                stage=HookStage.PRE_TOOL_USE,
                correlation_id=correlation_id,
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                purpose=body.purpose,
                action=intent_action,
                payload=event_payload,
            )
        )

        if not decision.allowed:
            logger.warning(
                "policy_denied",
                extra={
                    "correlation_id": correlation_id,
                    "agent_id": body.agent_id,
                    "customer_id": body.customer_id,
                    "stage": HookStage.PRE_TOOL_USE,
                    "action": body.intent_action,
                    "reason": decision.reason,
                    "details": decision.details,
                },
            )
            details: Dict[str, Any] = dict(decision.details or {})
            if decision.decision_id:
                details["decision_id"] = decision.decision_id

            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=decision.decision_id,
                    agent_id=body.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action=intent_action,
                    reason=decision.reason,
                    path=str(request.url.path),
                    details=details,
                )
            )

            raise PolicyEnforcementError(
                "Policy denied tool use",
                reason=decision.reason,
                details=details,
            )

    inp = SkillExecutionInput(
        theme=body.theme,
        brand_name=body.brand_name,
        offer=body.offer,
        location=body.location,
        audience=body.audience,
        tone=body.tone,
        language=body.language,
    )

    playbook = _marketing_multichannel_playbook()
    result = execute_marketing_multichannel_v1(playbook, inp)

    # Deterministic executor emits zero-token usage for now.
    events.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id=correlation_id,
            customer_id=body.customer_id,
            agent_id=body.agent_id,
            purpose=body.purpose,
            model=meter_model,
            cache_hit=meter_cache_hit,
            tokens_in=max(0, int(meter_tokens_in)),
            tokens_out=max(0, int(meter_tokens_out)),
            cost_usd=effective_estimated_cost_usd if effective_estimated_cost_usd > 0 else 0.0,
        )
    )

    return result
