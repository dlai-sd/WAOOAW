"""Integration smoke tests for TrialDimension/BudgetDimension exports (MOULD-GAP-1 E2-S2)."""


def test_trial_and_budget_dimensions_importable_from_agent_mold():
    from agent_mold import TrialDimension, BudgetDimension
    assert TrialDimension is not None
    assert BudgetDimension is not None


def test_lifecycle_hooks_importable_from_agent_mold():
    from agent_mold import AgentLifecycleHooks, NullLifecycleHooks, LifecycleContext
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    assert ctx.hired_instance_id == "hi-1"


def test_reference_agent_uses_trial_dimension():
    """Reference agents must use TrialDimension, not BasicDimension, for TRIAL."""
    from agent_mold.reference_agents import get_all_reference_agents
    from agent_mold.contracts import TrialDimension
    from agent_mold.spec import DimensionName

    agents = get_all_reference_agents()
    assert len(agents) > 0, "get_all_reference_agents() must return at least one agent"
    for a in agents:
        trial_dim = a.dimensions.get(DimensionName.TRIAL)
        if trial_dim is not None:
            assert isinstance(trial_dim, TrialDimension), (
                f"Agent {a.agent_id} uses {type(trial_dim)} for TRIAL — must be TrialDimension"
            )


def test_reference_agent_uses_budget_dimension():
    """Reference agents must use BudgetDimension, not BasicDimension, for BUDGET."""
    from agent_mold.reference_agents import get_all_reference_agents
    from agent_mold.contracts import BudgetDimension
    from agent_mold.spec import DimensionName

    agents = get_all_reference_agents()
    for a in agents:
        budget_dim = a.dimensions.get(DimensionName.BUDGET)
        if budget_dim is not None:
            assert isinstance(budget_dim, BudgetDimension), (
                f"Agent {a.agent_id} uses {type(budget_dim)} for BUDGET — must be BudgetDimension"
            )


def test_all_reference_agents_have_trial_dimension():
    """Every reference agent in the list must have a TRIAL dimension contract."""
    from agent_mold.reference_agents import get_all_reference_agents
    from agent_mold.contracts import TrialDimension
    from agent_mold.spec import DimensionName

    agents = get_all_reference_agents()
    for a in agents:
        trial_dim = a.dimensions.get(DimensionName.TRIAL)
        assert trial_dim is not None, f"Agent {a.agent_id} has no TRIAL dimension contract"
        assert isinstance(trial_dim, TrialDimension)
