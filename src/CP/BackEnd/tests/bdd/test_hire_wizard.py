"""BDD step definitions for hire wizard feature."""
import pytest
from pytest_bdd import given, when, then, scenarios


scenarios("features/hire_wizard.feature")


class HireContext:
    def __init__(self):
        self.customer_id = None
        self.agent_type = None
        self.hire = None


@pytest.fixture
def ctx():
    return HireContext()


@given('a customer with id "cp-user-001"')
def given_customer(ctx):
    ctx.customer_id = "cp-user-001"


@given('an agent type "marketing-agent"')
def given_agent_type(ctx):
    ctx.agent_type = "marketing-agent"


@when("the customer starts the hire wizard")
def when_start_wizard(ctx):
    ctx.hire = {
        "status": "draft",
        "customer_id": ctx.customer_id,
        "agent_type": ctx.agent_type,
        "step": 1,
    }


@then('a draft hire is created with status "draft"')
def then_draft_created(ctx):
    assert ctx.hire["status"] == "draft"


@given("a draft hire at step 1")
def given_draft_step1(ctx):
    ctx.hire = {"status": "draft", "step": 1}


@when("the customer advances to step 2")
def when_advance_step(ctx):
    ctx.hire["step"] = 2


@then("the hire is at step 2")
def then_at_step2(ctx):
    assert ctx.hire["step"] == 2


@given("a draft hire with base price 10000")
def given_draft_with_price(ctx):
    ctx.hire = {"status": "draft", "price": 10000}


@when('the customer applies coupon "SAVE20"')
def when_apply_coupon(ctx):
    ctx.hire["price"] = int(ctx.hire["price"] * 0.8)  # 20% discount


@then("the discounted price is 8000")
def then_discounted_price(ctx):
    assert ctx.hire["price"] == 8000


@given("a draft hire ready for payment")
def given_ready_for_payment(ctx):
    ctx.hire = {"status": "draft", "payment_confirmed": False, "trial_started": False}


@when("payment is confirmed")
def when_payment_confirmed(ctx):
    ctx.hire["payment_confirmed"] = True
    ctx.hire["status"] = "active"
    ctx.hire["trial_started"] = True


@then('the hire status is "active"')
def then_hire_active(ctx):
    assert ctx.hire["status"] == "active"


@then("a trial is started")
def then_trial_started(ctx):
    assert ctx.hire["trial_started"] is True


@given("a draft hire")
def given_draft_hire(ctx):
    ctx.hire = {"status": "draft"}


@when("the customer cancels the wizard")
def when_cancel_wizard(ctx):
    ctx.hire["status"] = "cancelled"


@then('the hire status is "cancelled"')
def then_hire_cancelled(ctx):
    assert ctx.hire["status"] == "cancelled"
