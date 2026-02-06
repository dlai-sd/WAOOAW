"""Goal 5: Reference agents end-to-end API.

This provides a minimal, testable surface to prove we can:
- manufacture agents from AgentSpecs
- run work through the same hooks + metering + usage events
- enforce publish approvals and trial restrictions
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.reference_agents import REFERENCE_AGENTS, get_reference_agent
from agent_mold.spec import DimensionName
from api.v1.agent_mold import ExecuteMarketingMultichannelRequest, execute_marketing_multichannel_post_v1
from core.exceptions import PolicyEnforcementError, UsageLimitError
from services.metering import (
    compute_effective_estimated_cost_usd,
    enforce_trial_and_budget,
    plan_enforces_budget,
    verify_trusted_metering_envelope_headers,
)
from services.usage_ledger import UsageLedger
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType
from api.v1.agent_mold import get_usage_ledger, get_usage_event_store
from services.policy_denial_audit import (
    PolicyDenialAuditRecord,
    PolicyDenialAuditStore,
    get_policy_denial_audit_store,
)


router = APIRouter(prefix="/reference-agents", tags=["reference-agents"])


class ReferenceAgentPublic(BaseModel):
    agent_id: str
    display_name: str
    agent_type: str
    spec: Dict[str, Any]


class TutorLessonPlanResult(BaseModel):
    subject: str
    level: str
    topic: str
    objectives: List[str]
    whiteboard_steps: List[str]
    quiz_questions: List[Dict[str, Any]]


class RunReferenceAgentRequest(BaseModel):
    class Config:
        extra = "forbid"

    customer_id: Optional[str] = None
    trial_mode: bool = False
    plan_id: Optional[str] = None

    # Optional publish stage
    do_publish: bool = False
    # Optional autopublish: only allowed if AgentSpec permits it.
    autopublish: bool = False
    approval_id: Optional[str] = None

    # Explicit intent for external side effects (fail closed).
    intent_action: Optional[str] = None

    # Metering payload (from AI Explorer)
    estimated_cost_usd: float = 0.0
    meter_tokens_in: int = 0
    meter_tokens_out: int = 0
    meter_model: Optional[str] = None
    meter_cache_hit: bool = False

    # Optional overrides
    theme: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None

    # Trading (MVP): manual futures intent contract
    exchange_account_id: Optional[str] = None
    coin: Optional[str] = None
    units: Optional[float] = None
    side: Optional[str] = None  # long|short
    action: Optional[str] = None  # enter|exit
    limit_price: Optional[float] = None
    market: Optional[bool] = None

    purpose: Optional[str] = None
    correlation_id: Optional[str] = None


class RunReferenceAgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    status: str = "draft"
    review: Optional[Dict[str, Any]] = None
    draft: Dict[str, Any]
    published: bool = False


@router.get("", response_model=List[ReferenceAgentPublic])
async def list_reference_agents() -> List[ReferenceAgentPublic]:
    return [
        ReferenceAgentPublic(
            agent_id=a.agent_id,
            display_name=a.display_name,
            agent_type=a.agent_type,
            spec=a.spec.model_dump(mode="json"),
        )
        for a in REFERENCE_AGENTS
    ]


def _tutor_deterministic_lesson_plan(
    *,
    subject: str,
    level: str,
    topic: str,
    language: str,
) -> TutorLessonPlanResult:
    # Deterministic, UI-ready steps (whiteboard prompts).
    objectives = [
        f"Understand {topic}",
        "Solve 3 example problems",
        "Check understanding with a short quiz",
    ]

    whiteboard_steps = [
        f"Write title: {topic}",
        "Define variables x and y",
        "Show standard form: ax + by = c",
        "Work through Example 1 with substitutions",
        "Ask student to solve Example 2",
        "Summarize key steps and common mistakes",
    ]

    quiz_questions = [
        {
            "q": "Which of the following is a linear equation in two variables?",
            "choices": ["x^2 + y = 1", "2x + 3y = 6", "xy = 5", "x + y^2 = 7"],
            "answer": "2x + 3y = 6",
        },
        {
            "q": "If 2x + y = 5 and x = 2, what is y?",
            "choices": ["1", "2", "3", "4"],
            "answer": "1",
        },
    ]

    return TutorLessonPlanResult(
        subject=subject,
        level=level,
        topic=topic,
        objectives=objectives,
        whiteboard_steps=whiteboard_steps,
        quiz_questions=quiz_questions,
    )


class TutorUIEventType(str, Enum):
    WHITEBOARD_STEP = "whiteboard_step"
    QUIZ_QUESTION = "quiz_question"


def _tutor_ui_event_stream(lesson: TutorLessonPlanResult) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for i, step in enumerate(lesson.whiteboard_steps):
        events.append(
            {
                "type": TutorUIEventType.WHITEBOARD_STEP.value,
                "index": i,
                "text": step,
            }
        )

    for i, q in enumerate(lesson.quiz_questions):
        events.append(
            {
                "type": TutorUIEventType.QUIZ_QUESTION.value,
                "index": i,
                "q": q.get("q"),
                "choices": q.get("choices") or [],
                "answer": q.get("answer"),
            }
        )

    return events


@router.post("/{agent_id}/run", response_model=RunReferenceAgentResponse)
async def run_reference_agent(
    agent_id: str,
    body: RunReferenceAgentRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    ledger: UsageLedger = Depends(get_usage_ledger),
    events: UsageEventStore = Depends(get_usage_event_store),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> RunReferenceAgentResponse:
    agent = get_reference_agent(agent_id)
    if agent is None:
        raise PolicyEnforcementError("Unknown reference agent", reason="unknown_reference_agent")

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

    # Shared metering enforcement for *any* reference agent execution.
    effective_cost = compute_effective_estimated_cost_usd(
        estimated_cost_usd=estimated_cost_usd,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        meter_model=meter_model,
    )

    should_publish = bool(body.do_publish or body.autopublish)

    if body.autopublish:
        skill_dim = agent.spec.dimensions.get(DimensionName.SKILL)
        autopublish_allowed = bool(
            skill_dim and (skill_dim.config or {}).get("autopublish_allowed") is True
        )
        if not autopublish_allowed:
            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=None,
                    agent_id=agent.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action="publish",
                    reason="autopublish_not_allowed",
                    path=str(request.url.path),
                    details={
                        "agent_id": agent.agent_id,
                    },
                )
            )
            raise PolicyEnforcementError(
                "Autopublish not allowed for agent",
                reason="autopublish_not_allowed",
                details={
                    "agent_id": agent.agent_id,
                },
            )

    enforce_trial_and_budget(
        correlation_id=correlation_id,
        agent_id=agent.agent_id,
        customer_id=body.customer_id,
        plan_id=body.plan_id,
        trial_mode=body.trial_mode,
        intent_action="publish" if should_publish else None,
        effective_estimated_cost_usd=effective_cost,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        purpose=body.purpose,
        ledger=ledger,
        events=events,
    )

    if agent.agent_type == "marketing":
        theme = body.theme or "5 posts/week campaign"
        req = ExecuteMarketingMultichannelRequest(
            agent_id=agent.agent_id,
            customer_id=body.customer_id,
            trial_mode=body.trial_mode,
            plan_id=body.plan_id,
            estimated_cost_usd=estimated_cost_usd,
            meter_tokens_in=meter_tokens_in,
            meter_tokens_out=meter_tokens_out,
            meter_model=meter_model,
            meter_cache_hit=meter_cache_hit,
            purpose=body.purpose,
            correlation_id=correlation_id,
            theme=theme,
            brand_name=agent.defaults.get("brand_name", "Brand"),
            location=agent.defaults.get("location"),
            audience=agent.defaults.get("audience"),
            tone=agent.defaults.get("tone"),
            language=body.language or agent.defaults.get("language"),
        )

        result = await execute_marketing_multichannel_post_v1(
            body=req,
            request=request,
            x_correlation_id=x_correlation_id,
            ledger=ledger,
            events=events,
        )
        draft: Dict[str, Any] = result.model_dump(mode="json")
    elif agent.agent_type == "tutor":
        lesson = _tutor_deterministic_lesson_plan(
            subject=agent.defaults.get("subject", "Subject"),
            level=agent.defaults.get("level", "Level"),
            topic=body.topic or agent.defaults.get("topic", "Topic"),
            language=body.language or agent.defaults.get("language", "en"),
        )

        # Record a usage event for tutor execution too.
        events.append(
            UsageEvent(
                event_type=UsageEventType.SKILL_EXECUTION,
                correlation_id=correlation_id,
                customer_id=body.customer_id,
                agent_id=agent.agent_id,
                purpose=body.purpose,
                action="lesson_plan",
                model=meter_model,
                cache_hit=meter_cache_hit,
                tokens_in=max(0, int(meter_tokens_in)),
                tokens_out=max(0, int(meter_tokens_out)),
                cost_usd=effective_cost if effective_cost > 0 else 0.0,
            )
        )

        draft = lesson.model_dump(mode="json")
        # Goal 5 / Epic 5.3: deterministic UI event stream contract.
        draft["ui_event_stream"] = _tutor_ui_event_stream(lesson)
    elif agent.agent_type == "trading":
        intent_action = (body.intent_action or "").strip().lower() or None
        if intent_action is not None and intent_action not in {"place_order", "close_position"}:
            raise HTTPException(status_code=422, detail="intent_action must be one of ['place_order','close_position']")

        # If a side-effect intent is requested, enforce approval and run hooks.
        if intent_action in {"place_order", "close_position"}:
            if not body.approval_id:
                raise PolicyEnforcementError(
                    "Missing approval_id for trading side effect",
                    reason="approval_required",
                    details={
                        "action": intent_action,
                    },
                )

            decision = default_hook_bus().emit(
                HookEvent(
                    stage=HookStage.PRE_TOOL_USE,
                    correlation_id=correlation_id,
                    agent_id=agent.agent_id,
                    customer_id=body.customer_id,
                    purpose=body.purpose,
                    action=intent_action,
                    payload={"approval_id": body.approval_id},
                )
            )
            if not decision.allowed:
                details: Dict[str, Any] = dict(decision.details or {})
                if decision.decision_id:
                    details["decision_id"] = decision.decision_id

                policy_audit.append(
                    PolicyDenialAuditRecord(
                        correlation_id=correlation_id,
                        decision_id=decision.decision_id,
                        agent_id=agent.agent_id,
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

        missing: List[str] = []
        if not body.exchange_account_id:
            missing.append("exchange_account_id")
        if not body.coin:
            missing.append("coin")
        if body.units is None:
            missing.append("units")
        if not body.side:
            missing.append("side")
        if not body.action:
            missing.append("action")

        if missing:
            raise HTTPException(status_code=422, detail=f"Missing required trading fields: {', '.join(missing)}")

        coin = str(body.coin).strip().upper()
        if not coin:
            raise HTTPException(status_code=422, detail="coin must be a non-empty string")

        try:
            units = float(body.units)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="units must be a number")
        if units <= 0:
            raise HTTPException(status_code=422, detail="units must be > 0")

        side = str(body.side).strip().lower()
        if side not in {"long", "short"}:
            raise HTTPException(status_code=422, detail="side must be one of ['long','short']")

        action = str(body.action).strip().lower()
        if action not in {"enter", "exit"}:
            raise HTTPException(status_code=422, detail="action must be one of ['enter','exit']")

        market = True if body.market is None else bool(body.market)
        limit_price = body.limit_price
        if not market:
            if limit_price is None:
                raise HTTPException(status_code=422, detail="limit_price is required when market=false")
            try:
                limit_price_value = float(limit_price)
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail="limit_price must be a number")
            if limit_price_value <= 0:
                raise HTTPException(status_code=422, detail="limit_price must be > 0")

        # MVP: return a deterministic draft plan (execution comes in later stories).
        draft = {
            "exchange_provider": agent.defaults.get("exchange_provider", "delta_exchange_india"),
            "exchange_account_id": body.exchange_account_id,
            "coin": coin,
            "units": units,
            "side": side,
            "action": action,
            "order_type": "market" if market else "limit",
            "limit_price": None if market else float(body.limit_price),
            "risk_checks": {
                "require_customer_approval": True,
            },
        }

        if intent_action:
            draft["intent_action"] = intent_action
        if body.approval_id:
            draft["approval_id"] = body.approval_id

        events.append(
            UsageEvent(
                event_type=UsageEventType.SKILL_EXECUTION,
                correlation_id=correlation_id,
                customer_id=body.customer_id,
                agent_id=agent.agent_id,
                purpose=body.purpose,
                action=intent_action or "draft_trade_plan",
                model=None,
                cache_hit=False,
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
            )
        )
    else:
        raise PolicyEnforcementError(
            "Unsupported reference agent type",
            reason="unsupported_reference_agent_type",
            details={
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
            },
        )

    published = False
    if should_publish:
        if body.trial_mode:
            # Should already be blocked by enforce_trial_and_budget (intent_action="publish"),
            # but keep this explicit for clarity.
            raise UsageLimitError(
                "Production write actions are blocked in trial mode",
                reason="trial_production_write_blocked",
            )

        event_payload: Dict[str, Any] = {}
        if body.approval_id:
            event_payload["approval_id"] = body.approval_id
        if body.autopublish:
            event_payload["autopublish"] = True

        decision = default_hook_bus().emit(
            HookEvent(
                stage=HookStage.PRE_TOOL_USE,
                correlation_id=correlation_id,
                agent_id=agent.agent_id,
                customer_id=body.customer_id,
                purpose=body.purpose,
                action="publish",
                payload=event_payload,
            )
        )
        if not decision.allowed:
            details: Dict[str, Any] = dict(decision.details or {})
            if decision.decision_id:
                details["decision_id"] = decision.decision_id

            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=decision.decision_id,
                    agent_id=agent.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action="publish",
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
        published = True

        # Record publish action as a usage event (no LLM metering implied).
        events.append(
            UsageEvent(
                event_type=UsageEventType.PUBLISH_ACTION,
                correlation_id=correlation_id,
                customer_id=body.customer_id,
                agent_id=agent.agent_id,
                purpose=body.purpose,
                model=None,
                cache_hit=False,
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
            )
        )

    # Minimal draft → review → publish state-machine stub.
    status = "draft"
    review: Optional[Dict[str, Any]] = None
    if body.approval_id and not should_publish:
        status = "in_review"
        review = {"approval_id": body.approval_id}
    if published:
        status = "published"
        review = {"approval_id": body.approval_id} if body.approval_id else review

    return RunReferenceAgentResponse(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        status=status,
        review=review,
        draft=draft,
        published=published,
    )
