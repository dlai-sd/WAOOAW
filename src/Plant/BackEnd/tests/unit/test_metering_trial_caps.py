from datetime import datetime, timezone

import pytest

from core.exceptions import UsageLimitError
from services.metering import enforce_trial_and_budget
from services.usage_events import InMemoryUsageEventStore
from services.usage_ledger import InMemoryUsageLedger


def test_trial_tasks_cap_resets_at_next_utc_midnight():
    ledger = InMemoryUsageLedger()
    events = InMemoryUsageEventStore()

    now = datetime(2026, 2, 5, 23, 59, 0, tzinfo=timezone.utc)

    for _ in range(10):
        enforce_trial_and_budget(
            correlation_id="corr",
            agent_id="AGT-1",
            customer_id="CUST-1",
            plan_id=None,
            trial_mode=True,
            intent_action=None,
            effective_estimated_cost_usd=0.0,
            meter_tokens_in=0,
            meter_tokens_out=0,
            purpose="demo",
            ledger=ledger,
            events=events,
            now=now,
        )

    with pytest.raises(UsageLimitError) as excinfo:
        enforce_trial_and_budget(
            correlation_id="corr",
            agent_id="AGT-1",
            customer_id="CUST-1",
            plan_id=None,
            trial_mode=True,
            intent_action=None,
            effective_estimated_cost_usd=0.0,
            meter_tokens_in=0,
            meter_tokens_out=0,
            purpose="demo",
            ledger=ledger,
            events=events,
            now=now,
        )

    err = excinfo.value
    assert err.reason == "trial_daily_cap"
    assert err.details["window_resets_at"] == "2026-02-06T00:00:00+00:00"


def test_trial_token_cap_denies_and_resets_at_next_utc_midnight(monkeypatch):
    monkeypatch.setenv("TRIAL_TOKENS_PER_DAY_CAP", "50")

    ledger = InMemoryUsageLedger()
    events = InMemoryUsageEventStore()

    now = datetime(2026, 2, 5, 23, 59, 0, tzinfo=timezone.utc)

    with pytest.raises(UsageLimitError) as excinfo:
        enforce_trial_and_budget(
            correlation_id="corr",
            agent_id="AGT-1",
            customer_id="CUST-1",
            plan_id=None,
            trial_mode=True,
            intent_action=None,
            effective_estimated_cost_usd=0.0,
            meter_tokens_in=30,
            meter_tokens_out=30,
            purpose="demo",
            ledger=ledger,
            events=events,
            now=now,
        )

    err = excinfo.value
    assert err.reason == "trial_daily_token_cap"
    assert err.details["window_resets_at"] == "2026-02-06T00:00:00+00:00"


def test_monthly_budget_resets_at_first_of_next_month(monkeypatch):
    # Force a deterministic plan budget without relying on template contents.
    import services.metering as metering

    monkeypatch.setattr(metering, "get_query_budget_monthly_usd", lambda _: 10.0)

    ledger = InMemoryUsageLedger()
    events = InMemoryUsageEventStore()

    now = datetime(2026, 1, 31, 23, 0, 0, tzinfo=timezone.utc)

    enforce_trial_and_budget(
        correlation_id="corr-1",
        agent_id="AGT-1",
        customer_id="CUST-1",
        plan_id="plan_starter",
        trial_mode=False,
        intent_action=None,
        effective_estimated_cost_usd=6.0,
        meter_tokens_in=0,
        meter_tokens_out=0,
        purpose="demo",
        ledger=ledger,
        events=events,
        now=now,
    )

    with pytest.raises(UsageLimitError) as excinfo:
        enforce_trial_and_budget(
            correlation_id="corr-2",
            agent_id="AGT-1",
            customer_id="CUST-1",
            plan_id="plan_starter",
            trial_mode=False,
            intent_action=None,
            effective_estimated_cost_usd=6.0,
            meter_tokens_in=0,
            meter_tokens_out=0,
            purpose="demo",
            ledger=ledger,
            events=events,
            now=now,
        )

    err = excinfo.value
    assert err.reason == "monthly_budget_exceeded"
    assert err.details["window_resets_at"] == "2026-02-01T00:00:00+00:00"
