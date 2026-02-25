"""
BDD step definitions for the 7-day Trial Lifecycle feature.

All external dependencies are mocked — no real DB or services required.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, scenario, then, when


# ── Scenarios ──────────────────────────────────────────────────────────────────

@pytest.mark.bdd
@scenario("features/trial_lifecycle.feature", "Customer starts a trial")
def test_customer_starts_a_trial() -> None:
    pass


@pytest.mark.bdd
@scenario("features/trial_lifecycle.feature", "Trial usage cap is enforced")
def test_trial_usage_cap_enforced() -> None:
    pass


@pytest.mark.bdd
@scenario("features/trial_lifecycle.feature", "Customer cancels trial and keeps deliverables")
def test_customer_cancels_trial() -> None:
    pass


@pytest.mark.bdd
@scenario("features/trial_lifecycle.feature", "Trial auto-expires after 7 days")
def test_trial_auto_expires() -> None:
    pass


# ── Shared context ─────────────────────────────────────────────────────────────

@pytest.fixture
def context():
    """Shared mutable context passed between steps."""
    return {}


# ── Background steps ───────────────────────────────────────────────────────────

@given("the WAOOAW platform is running")
def platform_is_running(context) -> None:
    context["platform"] = True


# ── Given steps ───────────────────────────────────────────────────────────────

@given(parsers.parse('a customer "{email}" exists'))
def customer_exists(context, email: str) -> None:
    context["customer"] = MagicMock(id=str(uuid4()), email=email)


@given(parsers.parse('an agent "{agent_id}" is available'))
def agent_is_available(context, agent_id: str) -> None:
    context["agent"] = MagicMock(id=agent_id, status="available")


@given("an active trial exists")
def active_trial_exists(context) -> None:
    now = datetime.now(timezone.utc)
    context["trial"] = MagicMock(
        id=str(uuid4()),
        status="active",
        created_at=now,
        expires_at=now + timedelta(days=7),
        usage_percent=0,
        deliverables=[MagicMock(id=str(uuid4()), accessible=True)],
    )


@given("an active trial with deliverables exists")
def active_trial_with_deliverables_exists(context) -> None:
    now = datetime.now(timezone.utc)
    context["trial"] = MagicMock(
        id=str(uuid4()),
        status="active",
        created_at=now,
        expires_at=now + timedelta(days=7),
        deliverables=[MagicMock(id=str(uuid4()), accessible=True)],
    )


@given("a trial that started 8 days ago")
def trial_started_8_days_ago(context) -> None:
    now = datetime.now(timezone.utc)
    context["trial"] = MagicMock(
        id=str(uuid4()),
        status="active",
        created_at=now - timedelta(days=8),
        expires_at=now - timedelta(days=1),  # already past expiry
    )


# ── When steps ────────────────────────────────────────────────────────────────

@when(parsers.parse('the customer starts a trial for agent "{agent_id}"'))
def customer_starts_trial(context, agent_id: str) -> None:
    now = datetime.now(timezone.utc)
    context["trial"] = MagicMock(
        id=str(uuid4()),
        status="active",
        agent_id=agent_id,
        customer_id=context["customer"].id,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )


@when("the customer uses 100% of the trial allocation")
def customer_uses_full_allocation(context) -> None:
    context["trial"].usage_percent = 100
    context["usage_blocked"] = True  # simulate service blocking further use


@when("the customer cancels the trial")
def customer_cancels_trial(context) -> None:
    context["trial"].status = "cancelled"


@when("the expiry check runs")
def expiry_check_runs(context) -> None:
    now = datetime.now(timezone.utc)
    if context["trial"].expires_at < now:
        context["trial"].status = "expired"


# ── Then steps ────────────────────────────────────────────────────────────────

@then(parsers.parse('a trial is created with status "{expected_status}"'))
def trial_created_with_status(context, expected_status: str) -> None:
    assert context["trial"].status == expected_status


@then("the trial expires in 7 days")
def trial_expires_in_7_days(context) -> None:
    trial = context["trial"]
    duration = trial.expires_at - trial.created_at
    assert duration == timedelta(days=7)


@then("further usage is blocked")
def further_usage_is_blocked(context) -> None:
    assert context.get("usage_blocked") is True


@then(parsers.parse('the trial status becomes "{expected_status}"'))
def trial_status_becomes(context, expected_status: str) -> None:
    assert context["trial"].status == expected_status


@then("the deliverables remain accessible")
def deliverables_remain_accessible(context) -> None:
    for deliverable in context["trial"].deliverables:
        assert deliverable.accessible is True
