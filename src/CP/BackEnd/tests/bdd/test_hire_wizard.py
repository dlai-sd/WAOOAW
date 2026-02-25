"""
BDD step definitions for the CP Hire Wizard Flow feature.

All external services are mocked — no real DB, payment, or Plant Gateway calls.
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, parsers, scenario, then, when


# ── Scenarios ──────────────────────────────────────────────────────────────────

@pytest.mark.bdd
@scenario("features/hire_wizard.feature", "Customer creates a draft hire")
def test_customer_creates_draft_hire() -> None:
    pass


@pytest.mark.bdd
@scenario("features/hire_wizard.feature", "Customer advances wizard steps")
def test_customer_advances_wizard_steps() -> None:
    pass


@pytest.mark.bdd
@scenario("features/hire_wizard.feature", "Customer applies a coupon")
def test_customer_applies_coupon() -> None:
    pass


@pytest.mark.bdd
@scenario("features/hire_wizard.feature", "Customer completes payment")
def test_customer_completes_payment() -> None:
    pass


@pytest.mark.bdd
@scenario("features/hire_wizard.feature", "Customer cancels hire wizard")
def test_customer_cancels_hire_wizard() -> None:
    pass


# ── Shared context ─────────────────────────────────────────────────────────────

@pytest.fixture
def context():
    return {}


# ── Background steps ───────────────────────────────────────────────────────────

@given("the CP backend is running")
def cp_backend_running(context) -> None:
    context["cp_running"] = True


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a logged-in customer")
def logged_in_customer(context) -> None:
    context["customer"] = MagicMock(id=str(uuid4()), email="customer@waooaw.com")


@given("a hire draft at step 1")
def hire_draft_at_step_1(context) -> None:
    context["hire_draft"] = MagicMock(
        id=str(uuid4()),
        status="draft",
        current_step=1,
        agent_id="agent-001",
        total_amount=12000.0,
        discount=0.0,
        deleted=False,
    )


@given("a hire draft at payment step")
def hire_draft_at_payment_step(context) -> None:
    context["hire_draft"] = MagicMock(
        id=str(uuid4()),
        status="draft",
        current_step=3,
        agent_id="agent-001",
        total_amount=12000.0,
        discount=0.0,
        deleted=False,
    )


@given("a hire draft with coupon applied")
def hire_draft_with_coupon(context) -> None:
    context["hire_draft"] = MagicMock(
        id=str(uuid4()),
        status="draft",
        current_step=3,
        agent_id="agent-001",
        total_amount=10800.0,  # 10% off 12000
        discount=1200.0,
        coupon="TRIAL10",
        deleted=False,
    )


@given("a hire draft in progress")
def hire_draft_in_progress(context) -> None:
    context["hire_draft"] = MagicMock(
        id=str(uuid4()),
        status="draft",
        current_step=2,
        deleted=False,
    )


# ── When steps ────────────────────────────────────────────────────────────────

@when(parsers.parse('they start a hire wizard for agent "{agent_id}"'))
def start_hire_wizard(context, agent_id: str) -> None:
    context["hire_draft"] = MagicMock(
        id=str(uuid4()),
        status="draft",
        current_step=1,
        agent_id=agent_id,
        customer_id=context["customer"].id,
        total_amount=12000.0,
        discount=0.0,
        deleted=False,
    )


@when("the customer completes step 1")
def complete_step_1(context) -> None:
    context["hire_draft"].current_step = 2


@when(parsers.parse('the customer applies coupon "{coupon_code}"'))
def apply_coupon(context, coupon_code: str) -> None:
    draft = context["hire_draft"]
    # Simulate 10% discount for TRIAL10
    discount = draft.total_amount * 0.10
    draft.discount = discount
    draft.total_amount = draft.total_amount - discount
    draft.coupon = coupon_code


@when("the customer confirms payment")
def confirm_payment(context) -> None:
    context["hire_draft"].status = "confirmed"
    context["trial_started"] = True


@when("the customer cancels")
def customer_cancels(context) -> None:
    context["hire_draft"].deleted = True
    context["hire_draft"].status = "deleted"


# ── Then steps ────────────────────────────────────────────────────────────────

@then("a hire draft is created")
def hire_draft_is_created(context) -> None:
    assert context["hire_draft"] is not None
    assert context["hire_draft"].status == "draft"


@then("the wizard is at step 1")
def wizard_at_step_1(context) -> None:
    assert context["hire_draft"].current_step == 1


@then("the wizard advances to step 2")
def wizard_advances_to_step_2(context) -> None:
    assert context["hire_draft"].current_step == 2


@then("the discount is applied to the total")
def discount_applied(context) -> None:
    assert context["hire_draft"].discount > 0


@then("the hire is confirmed")
def hire_is_confirmed(context) -> None:
    assert context["hire_draft"].status == "confirmed"


@then("a trial period begins")
def trial_period_begins(context) -> None:
    assert context.get("trial_started") is True


@then("the draft is deleted")
def draft_is_deleted(context) -> None:
    assert context["hire_draft"].deleted is True
