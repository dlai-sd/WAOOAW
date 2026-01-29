"""Metering helpers.

Goal 4/5: keep metering logic consistent across skill execution paths.

This is intentionally env-driven and in-process for now.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.exceptions import UsageLimitError
from services.plan_limits import get_query_budget_monthly_usd
from services.usage_ledger import UsageLedger
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType


def estimate_cost_usd_from_metering(*, tokens_in: int, tokens_out: int, model: Optional[str]) -> float:
    """Best-effort cost estimation.

    Uses `MODEL_PRICING_JSON`, formatted as:
    {"gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006}}
    """

    if not model:
        return 0.0

    raw = os.getenv("MODEL_PRICING_JSON")
    if not raw:
        return 0.0

    try:
        pricing = json.loads(raw)
        entry = pricing.get(model)
        if not isinstance(entry, dict):
            return 0.0
        inp = float(entry.get("input_per_1k", 0.0))
        outp = float(entry.get("output_per_1k", 0.0))
    except Exception:
        return 0.0

    tokens_in = max(0, int(tokens_in))
    tokens_out = max(0, int(tokens_out))
    return (tokens_in / 1000.0) * inp + (tokens_out / 1000.0) * outp


def compute_effective_estimated_cost_usd(
    *,
    estimated_cost_usd: float,
    meter_tokens_in: int,
    meter_tokens_out: int,
    meter_model: Optional[str],
) -> float:
    if estimated_cost_usd and estimated_cost_usd > 0:
        return float(estimated_cost_usd)

    return estimate_cost_usd_from_metering(
        tokens_in=meter_tokens_in,
        tokens_out=meter_tokens_out,
        model=meter_model,
    )


def enforce_trial_and_budget(
    *,
    correlation_id: str,
    agent_id: str,
    customer_id: Optional[str],
    plan_id: Optional[str],
    trial_mode: bool,
    intent_action: Optional[str],
    effective_estimated_cost_usd: float,
    meter_tokens_in: int,
    meter_tokens_out: int,
    purpose: Optional[str],
    ledger: UsageLedger,
    events: UsageEventStore,
    now: datetime | None = None,
) -> None:
    """Enforce trial caps/restrictions and monthly budget checks.

    Raises UsageLimitError on deny.
    """

    # =========================
    # Trial restrictions/caps
    # =========================
    if trial_mode:
        if not customer_id:
            raise UsageLimitError(
                "Trial metering requires customer_id",
                reason="customer_id_required",
            )

        # Trial restriction: production write actions are blocked.
        if intent_action:
            raise UsageLimitError(
                "Production write actions are blocked in trial mode",
                reason="trial_production_write_blocked",
                details={
                    "customer_id": customer_id,
                    "intent_action": intent_action,
                },
            )

        # Trial restriction: high-cost API calls are blocked (>$1 per call).
        if effective_estimated_cost_usd > 1.0:
            raise UsageLimitError(
                "High-cost calls are blocked in trial mode (>$1/call)",
                reason="trial_high_cost_call",
                details={
                    "customer_id": customer_id,
                    "estimated_cost_usd": effective_estimated_cost_usd,
                    "max_cost_usd": 1.0,
                },
            )

        # Trial caps: 10 tasks/day (per Trial Mode PEP spec).
        counter_key = f"trial_tasks_day:{customer_id}"
        counter_result = ledger.increment_with_limit(
            key=counter_key,
            limit=10,
            window=timedelta(days=1),
            amount=1,
            now=now,
        )

        if not counter_result.allowed:
            raise UsageLimitError(
                "Daily trial limit reached (10 tasks/day)",
                reason="trial_daily_cap",
                details={
                    "customer_id": customer_id,
                    "limit": 10,
                    "window_resets_at": counter_result.resets_at.isoformat(),
                },
            )

        # Optional token/day cap for trial (set by env var; default disabled).
        token_cap_raw = os.getenv("TRIAL_TOKENS_PER_DAY_CAP")
        if token_cap_raw:
            token_cap = int(token_cap_raw)
            token_amount = max(0, int(meter_tokens_in) + int(meter_tokens_out))
            if token_amount > 0:
                token_key = f"trial_tokens_day:{customer_id}"
                token_result = ledger.increment_with_limit(
                    key=token_key,
                    limit=token_cap,
                    window=timedelta(days=1),
                    amount=token_amount,
                    now=now,
                )
                if not token_result.allowed:
                    raise UsageLimitError(
                        "Daily trial token limit reached",
                        reason="trial_daily_token_cap",
                        details={
                            "customer_id": customer_id,
                            "limit": token_cap,
                            "window_resets_at": token_result.resets_at.isoformat(),
                        },
                    )

    # =========================
    # Monthly budget checks
    # =========================
    if customer_id and plan_id and effective_estimated_cost_usd > 0:
        budget = get_query_budget_monthly_usd(plan_id)
        if budget is not None:
            events.append(
                UsageEvent(
                    event_type=UsageEventType.BUDGET_PRECHECK,
                    correlation_id=correlation_id,
                    customer_id=customer_id,
                    agent_id=agent_id,
                    purpose=purpose,
                    cost_usd=0.0,
                )
            )

            spend_key = f"query_spend_month_usd:{customer_id}:{plan_id}"
            spend_result = ledger.add_spend_with_limit(
                key=spend_key,
                budget_usd=budget,
                spend_usd=effective_estimated_cost_usd,
                window=timedelta(days=30),
                now=now,
            )
            if not spend_result.allowed:
                raise UsageLimitError(
                    "Monthly query budget exceeded",
                    reason="monthly_budget_exceeded",
                    details={
                        "plan_id": plan_id,
                        "budget_usd": budget,
                        "current_spend_usd": spend_result.total_usd,
                        "attempted_spend_usd": effective_estimated_cost_usd,
                        "window_resets_at": spend_result.resets_at.isoformat(),
                    },
                )
