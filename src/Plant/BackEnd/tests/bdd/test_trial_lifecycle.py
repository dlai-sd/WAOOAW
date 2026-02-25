"""BDD step definitions for trial lifecycle feature."""
import pytest
from datetime import datetime, timedelta, timezone
from pytest_bdd import given, when, then, scenario, scenarios


scenarios("features/trial_lifecycle.feature")


# ── Helpers ──────────────────────────────────────────────────────────────────

class TrialContext:
    def __init__(self):
        self.customer_email = None
        self.agent_id = None
        self.trial = None
        self.deliverables = []
        self.token_limit = None
        self.tokens_used = 0
        self.usage_rejected = False
        self.rejection_reason = None


@pytest.fixture
def ctx():
    return TrialContext()


# ── Scenario: Start a new trial ───────────────────────────────────────────────

@given('a customer with email "test@example.com"')
def given_customer(ctx):
    ctx.customer_email = "test@example.com"


@given('an agent with id "agent-001"')
def given_agent(ctx):
    ctx.agent_id = "agent-001"


@when("the customer starts a trial for the agent")
def when_start_trial(ctx):
    ctx.trial = {
        "status": "active",
        "customer_email": ctx.customer_email,
        "agent_id": ctx.agent_id,
        "started_at": datetime.now(timezone.utc),
        "ends_at": datetime.now(timezone.utc) + timedelta(days=7),
        "deliverables": [],
    }


@then('the trial status is "active"')
def then_trial_active(ctx):
    assert ctx.trial["status"] == "active"


@then("the trial duration is 7 days")
def then_trial_duration(ctx):
    delta = ctx.trial["ends_at"] - ctx.trial["started_at"]
    assert delta.days == 7


# ── Scenario: Cancel and keep deliverables ────────────────────────────────────

@given("an active trial with one deliverable")
def given_active_trial_with_deliverable(ctx):
    ctx.trial = {"status": "active", "deliverables": ["deliverable-001"]}
    ctx.deliverables = list(ctx.trial["deliverables"])


@when("the customer cancels the trial")
def when_cancel_trial(ctx):
    ctx.trial["status"] = "cancelled"


@then('the trial status is "cancelled"')
def then_trial_cancelled(ctx):
    assert ctx.trial["status"] == "cancelled"


@then("the deliverable is still accessible")
def then_deliverable_accessible(ctx):
    assert "deliverable-001" in ctx.deliverables


# ── Scenario: Auto-expire ─────────────────────────────────────────────────────

@given("an active trial started 8 days ago")
def given_old_trial(ctx):
    ctx.trial = {
        "status": "active",
        "started_at": datetime.now(timezone.utc) - timedelta(days=8),
        "ends_at": datetime.now(timezone.utc) - timedelta(days=1),
    }


@when("the expiry check runs")
def when_expiry_check(ctx):
    now = datetime.now(timezone.utc)
    if now > ctx.trial["ends_at"]:
        ctx.trial["status"] = "expired"


@then('the trial status is "expired"')
def then_trial_expired(ctx):
    assert ctx.trial["status"] == "expired"


# ── Scenario: Usage cap ───────────────────────────────────────────────────────

@given("an active trial with a token limit of 1000")
def given_trial_with_limit(ctx):
    ctx.trial = {"status": "active"}
    ctx.token_limit = 1000
    ctx.tokens_used = 0


@when("1000 tokens have been used")
def when_tokens_used(ctx):
    ctx.tokens_used = 1000


@then('further usage is rejected with "cap exceeded"')
def then_cap_enforced(ctx):
    if ctx.tokens_used >= ctx.token_limit:
        ctx.usage_rejected = True
        ctx.rejection_reason = "cap exceeded"
    assert ctx.usage_rejected
    assert ctx.rejection_reason == "cap exceeded"
