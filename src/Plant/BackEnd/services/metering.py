"""Metering helpers.

Goal 4/5: keep metering logic consistent across skill execution paths.

This is intentionally env-driven and in-process for now.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
from typing import Mapping, Optional

from core.exceptions import UsageLimitError
from services.plan_limits import get_query_budget_monthly_usd
from services.usage_ledger import UsageLedger
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType


METERING_ENVELOPE_SECRET_ENV = "METERING_ENVELOPE_SECRET"
METERING_ENVELOPE_TTL_SECONDS_ENV = "METERING_ENVELOPE_TTL_SECONDS"


@dataclass(frozen=True)
class TrustedMeteringEnvelope:
    timestamp: int
    correlation_id: str
    tokens_in: int
    tokens_out: int
    model: Optional[str]
    cache_hit: bool
    cost_usd: float


@dataclass(frozen=True)
class TrustedMeteringVerification:
    enabled: bool
    status: str
    envelope: Optional[TrustedMeteringEnvelope]


def is_trusted_metering_enabled() -> bool:
    return bool(os.getenv(METERING_ENVELOPE_SECRET_ENV))


def plan_enforces_budget(plan_id: Optional[str]) -> bool:
    if not plan_id:
        return False
    return get_query_budget_monthly_usd(plan_id) is not None


def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _canonical_cost(cost_usd: float) -> str:
    try:
        value = Decimal(str(cost_usd)).quantize(Decimal("0.000001"))
    except (InvalidOperation, ValueError):
        value = Decimal("0")
    # Avoid exponent forms; keep a stable string.
    return format(value, "f")


def _canonical_cache_hit(cache_hit: bool) -> str:
    return "1" if bool(cache_hit) else "0"


def _canonical_metering_string(
    *,
    timestamp: int,
    correlation_id: str,
    tokens_in: int,
    tokens_out: int,
    model: Optional[str],
    cache_hit: bool,
    cost_usd: float,
) -> str:
    model_value = (model or "").strip()
    return "|".join(
        [
            str(int(timestamp)),
            str(correlation_id),
            str(int(tokens_in)),
            str(int(tokens_out)),
            model_value,
            _canonical_cache_hit(cache_hit),
            _canonical_cost(cost_usd),
        ]
    )


def sign_trusted_metering_envelope(
    *,
    secret: str,
    timestamp: int,
    correlation_id: str,
    tokens_in: int,
    tokens_out: int,
    model: Optional[str],
    cache_hit: bool,
    cost_usd: float,
) -> str:
    payload = _canonical_metering_string(
        timestamp=timestamp,
        correlation_id=correlation_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model=model,
        cache_hit=cache_hit,
        cost_usd=cost_usd,
    )
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_no_pad(digest)


def verify_trusted_metering_envelope_headers(
    *,
    headers: Mapping[str, str],
    correlation_id: str,
    now: datetime | None = None,
) -> TrustedMeteringVerification:
    """Verify metering fields sent by a trusted caller (AI Explorer).

    Contract (headers):
    - X-Metering-Timestamp: unix seconds
    - X-Metering-Tokens-In / X-Metering-Tokens-Out: ints
    - X-Metering-Model: string (optional; can be empty)
    - X-Metering-Cache-Hit: 0/1 (optional; defaults false)
    - X-Metering-Cost-USD: float (optional; defaults 0)
    - X-Metering-Signature: base64url(hmac_sha256(secret, canonical_string))
    Canonical string:
      ts|correlation_id|tokens_in|tokens_out|model|cache_hit|cost_usd(6dp)

    If the env var METERING_ENVELOPE_SECRET is not set, verification is disabled.
    """

    secret = os.getenv(METERING_ENVELOPE_SECRET_ENV, "")
    if not secret:
        return TrustedMeteringVerification(enabled=False, status="disabled", envelope=None)

    def _get(name: str) -> Optional[str]:
        # Starlette headers are case-insensitive; Mapping access should work.
        value = headers.get(name)
        return value if value is not None else headers.get(name.lower())

    signature = _get("X-Metering-Signature")
    timestamp_raw = _get("X-Metering-Timestamp")
    tokens_in_raw = _get("X-Metering-Tokens-In")
    tokens_out_raw = _get("X-Metering-Tokens-Out")
    model = _get("X-Metering-Model")
    cache_hit_raw = _get("X-Metering-Cache-Hit")
    cost_raw = _get("X-Metering-Cost-USD")

    present = any(
        v is not None
        for v in [
            signature,
            timestamp_raw,
            tokens_in_raw,
            tokens_out_raw,
            model,
            cache_hit_raw,
            cost_raw,
        ]
    )
    if not present:
        return TrustedMeteringVerification(enabled=True, status="missing", envelope=None)

    if not (signature and timestamp_raw and tokens_in_raw is not None and tokens_out_raw is not None):
        return TrustedMeteringVerification(enabled=True, status="bad_format", envelope=None)

    try:
        timestamp = int(timestamp_raw)
        tokens_in = int(tokens_in_raw)
        tokens_out = int(tokens_out_raw)
    except Exception:
        return TrustedMeteringVerification(enabled=True, status="bad_format", envelope=None)

    cache_hit = str(cache_hit_raw or "0").strip().lower() in {"1", "true", "yes"}
    try:
        cost_usd = float(cost_raw) if cost_raw is not None else 0.0
    except Exception:
        cost_usd = 0.0

    current_time = _normalize_now(now)
    ttl_seconds = int(os.getenv(METERING_ENVELOPE_TTL_SECONDS_ENV, "300") or "300")
    # Reject envelopes too far from 'now' (both past and future).
    if abs(int(current_time.timestamp()) - timestamp) > ttl_seconds:
        return TrustedMeteringVerification(enabled=True, status="stale", envelope=None)

    expected = sign_trusted_metering_envelope(
        secret=secret,
        timestamp=timestamp,
        correlation_id=correlation_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model=model,
        cache_hit=cache_hit,
        cost_usd=cost_usd,
    )
    if not hmac.compare_digest(str(signature).strip(), expected):
        return TrustedMeteringVerification(enabled=True, status="invalid", envelope=None)

    env = TrustedMeteringEnvelope(
        timestamp=timestamp,
        correlation_id=correlation_id,
        tokens_in=max(0, int(tokens_in)),
        tokens_out=max(0, int(tokens_out)),
        model=(model or None),
        cache_hit=bool(cache_hit),
        cost_usd=float(cost_usd),
    )
    return TrustedMeteringVerification(enabled=True, status="trusted", envelope=env)


def _normalize_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(tz=timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now


def _window_until_next_utc_day(now: datetime) -> timedelta:
    now = _normalize_now(now)
    # Next UTC midnight (calendar day boundary).
    next_midnight = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=1)
    delta = next_midnight - now
    # Defensive: should always be > 0, but never return a non-positive window.
    if delta <= timedelta(0):
        return timedelta(days=1)
    return delta


def _window_until_next_utc_month(now: datetime) -> timedelta:
    now = _normalize_now(now)
    # Next UTC month boundary (first of next month at 00:00).
    if now.month == 12:
        boundary = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        boundary = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    # If exactly at the boundary, roll to the following month.
    if now >= boundary:
        if boundary.month == 12:
            boundary = datetime(boundary.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            boundary = datetime(boundary.year, boundary.month + 1, 1, tzinfo=timezone.utc)

    delta = boundary - now
    if delta <= timedelta(0):
        # Fallback: month windows should never be non-positive.
        return timedelta(days=31)
    return delta


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

    current_time = _normalize_now(now)

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
            window=_window_until_next_utc_day(current_time),
            amount=1,
            now=current_time,
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
                    window=_window_until_next_utc_day(current_time),
                    amount=token_amount,
                    now=current_time,
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
    if customer_id and plan_id:
        budget = get_query_budget_monthly_usd(plan_id)
        if budget is not None:
            # Fail closed: if budgets are configured for a plan, callers must
            # provide metering that can produce a positive cost estimate.
            if effective_estimated_cost_usd <= 0:
                raise UsageLimitError(
                    "Metering is required for budget enforcement",
                    reason="metering_required_for_budget",
                    details={
                        "customer_id": customer_id,
                        "plan_id": plan_id,
                    },
                )

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
                window=_window_until_next_utc_month(current_time),
                now=current_time,
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
