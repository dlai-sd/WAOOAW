"""Unit tests for ConstructBindings + ConstraintPolicy in AgentSpec (PLANT-MOULD-1 E1-S2)."""
import pytest

from agent_mold.pump import GoalConfigPump
from agent_mold.processor import BaseProcessor
from agent_mold.spec import AgentSpec, ApprovalMode, ConstructBindings, ConstraintPolicy


class DummyProcessor(BaseProcessor):
    async def process(self, input_data, hook_bus):
        return None


class DummyScheduler:
    pass


def make_bindings(**overrides):
    defaults = dict(
        processor_class=DummyProcessor,
        scheduler_class=DummyScheduler,
        pump_class=GoalConfigPump,
    )
    return ConstructBindings(**{**defaults, **overrides})


def test_bindings_validate_ok():
    b = make_bindings()
    b.validate()  # should not raise


def test_bindings_validate_fail_bad_processor():
    b = make_bindings(processor_class=object)
    with pytest.raises(TypeError):
        b.validate()


def test_bindings_validate_fail_bad_pump():
    b = make_bindings(pump_class=object)
    with pytest.raises(TypeError):
        b.validate()


def test_constraint_policy_defaults():
    cp = ConstraintPolicy()
    assert cp.approval_mode == ApprovalMode.MANUAL
    assert cp.trial_task_limit == 10
    assert cp.max_tasks_per_day == 0
    assert cp.max_position_size_inr == 0.0


def test_agent_spec_has_bindings_field():
    spec = AgentSpec(agent_id="AGT-TEST-001", agent_type="test")
    assert hasattr(spec, "bindings")
    assert hasattr(spec, "constraint_policy")


def test_agent_spec_bindings_default_none():
    spec = AgentSpec(agent_id="AGT-TEST-001", agent_type="test")
    assert spec.bindings is None


def test_agent_spec_constraint_policy_default():
    spec = AgentSpec(agent_id="AGT-TEST-001", agent_type="test")
    assert isinstance(spec.constraint_policy, ConstraintPolicy)
    assert spec.constraint_policy.approval_mode == ApprovalMode.MANUAL


def test_agent_spec_with_bindings():
    b = make_bindings()
    spec = AgentSpec(
        agent_id="AGT-TEST-001",
        agent_type="test",
        bindings=b,
    )
    assert spec.bindings is b
    spec.bindings.validate()


def test_reference_agents_have_bindings():
    from agent_mold.reference_agents import trading_agent
    assert trading_agent.bindings is not None
    trading_agent.bindings.validate()


def test_reference_agent_marketing_has_bindings():
    from agent_mold.reference_agents import marketing_agent
    assert marketing_agent.bindings is not None
    marketing_agent.bindings.validate()


def test_reference_agent_tutor_has_bindings():
    from agent_mold.reference_agents import tutor_agent
    assert tutor_agent.bindings is not None
    tutor_agent.bindings.validate()


def test_digital_marketing_agent_contract_exposes_visible_skills_and_youtube_destination():
    from agent_mold.reference_agents import digital_marketing_agent

    skill_dimension = digital_marketing_agent.spec.dimensions[digital_marketing_agent.spec.dimensions.keys().__iter__().__next__()]
    assert skill_dimension is not None

    skill_config = digital_marketing_agent.spec.dimensions[
        next(name for name in digital_marketing_agent.spec.dimensions.keys() if name.value == "skill")
    ].config
    assert skill_config["visible_skills"] == [
        "Theme Discovery",
        "Content Creation",
        "Content Publishing",
    ]
    assert skill_config["supported_live_destinations"] == ["youtube"]
