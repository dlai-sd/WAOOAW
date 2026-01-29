"""Goal 5: Reference agents end-to-end API.

This provides a minimal, testable surface to prove we can:
- manufacture agents from AgentSpecs
- run work through the same hooks + metering + usage events
- enforce publish approvals and trial restrictions
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.reference_agents import REFERENCE_AGENTS, get_reference_agent
from api.v1.agent_mold import ExecuteMarketingMultichannelRequest, execute_marketing_multichannel_post_v1
from core.exceptions import PolicyEnforcementError, UsageLimitError
from services.metering import compute_effective_estimated_cost_usd, enforce_trial_and_budget
from services.usage_ledger import UsageLedger
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType
from api.v1.agent_mold import get_usage_ledger, get_usage_event_store


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
    customer_id: Optional[str] = None
    trial_mode: bool = False
    plan_id: Optional[str] = None

    # Optional publish stage
    do_publish: bool = False
    approval_id: Optional[str] = None

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

    purpose: Optional[str] = None
    correlation_id: Optional[str] = None


class RunReferenceAgentResponse(BaseModel):
    agent_id: str
    agent_type: str
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


@router.post("/{agent_id}/run", response_model=RunReferenceAgentResponse)
async def run_reference_agent(
    agent_id: str,
    body: RunReferenceAgentRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    ledger: UsageLedger = Depends(get_usage_ledger),
    events: UsageEventStore = Depends(get_usage_event_store),
) -> RunReferenceAgentResponse:
    agent = get_reference_agent(agent_id)
    if agent is None:
        raise PolicyEnforcementError("Unknown reference agent", reason="unknown_reference_agent")

    correlation_id = body.correlation_id or x_correlation_id or str(id(request))

    # Shared metering enforcement for *any* reference agent execution.
    effective_cost = compute_effective_estimated_cost_usd(
        estimated_cost_usd=body.estimated_cost_usd,
        meter_tokens_in=body.meter_tokens_in,
        meter_tokens_out=body.meter_tokens_out,
        meter_model=body.meter_model,
    )

    enforce_trial_and_budget(
        correlation_id=correlation_id,
        agent_id=agent.agent_id,
        customer_id=body.customer_id,
        plan_id=body.plan_id,
        trial_mode=body.trial_mode,
        intent_action="publish" if body.do_publish else None,
        effective_estimated_cost_usd=effective_cost,
        meter_tokens_in=body.meter_tokens_in,
        meter_tokens_out=body.meter_tokens_out,
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
            estimated_cost_usd=body.estimated_cost_usd,
            meter_tokens_in=body.meter_tokens_in,
            meter_tokens_out=body.meter_tokens_out,
            meter_model=body.meter_model,
            meter_cache_hit=body.meter_cache_hit,
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
    else:
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
                model=body.meter_model,
                cache_hit=body.meter_cache_hit,
                tokens_in=max(0, int(body.meter_tokens_in)),
                tokens_out=max(0, int(body.meter_tokens_out)),
                cost_usd=effective_cost if effective_cost > 0 else 0.0,
            )
        )

        draft = lesson.model_dump(mode="json")

    published = False
    if body.do_publish:
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
            raise PolicyEnforcementError(
                "Policy denied tool use",
                reason=decision.reason,
                details=decision.details,
            )
        published = True

    return RunReferenceAgentResponse(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        draft=draft,
        published=published,
    )
