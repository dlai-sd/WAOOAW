"""Tests for TrialDimension and BudgetDimension enforcement (MOULD-GAP-1 E2-S1)."""
import pytest
from unittest.mock import MagicMock
from agent_mold.contracts import TrialDimension, BudgetDimension
from agent_mold.hooks import HookBus, HookStage


def _make_event(tasks_used=0, tasks_today=0):
    event = MagicMock()
    event.tasks_used = tasks_used
    event.tasks_today = tasks_today
    return event


# ── TrialDimension tests ────────────────────────────────────────────────────

def test_trial_dimension_registers_hook_on_hookbus():
    dim = TrialDimension(trial_task_limit=5)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 1


def test_trial_quota_hook_allows_when_under_limit():
    dim = TrialDimension(trial_task_limit=10)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=5)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is True


def test_trial_quota_hook_denies_when_at_limit():
    dim = TrialDimension(trial_task_limit=10)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=10)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False
    assert "trial_task_limit" in decision.reason


def test_trial_quota_hook_denies_when_over_limit():
    dim = TrialDimension(trial_task_limit=5)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=7)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False


def test_trial_dimension_validate_rejects_zero_limit():
    dim = TrialDimension(trial_task_limit=0)
    with pytest.raises(ValueError, match="trial_task_limit"):
        dim.validate(MagicMock())


def test_trial_dimension_validate_accepts_valid_limit():
    dim = TrialDimension(trial_task_limit=5)
    dim.validate(MagicMock())  # must not raise


# ── BudgetDimension tests ───────────────────────────────────────────────────

def test_budget_dimension_zero_registers_no_hook():
    """max_tasks_per_day=0 means unlimited — no hook should be registered."""
    dim = BudgetDimension(max_tasks_per_day=0)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 0


def test_budget_dimension_registers_hook_when_limit_set():
    dim = BudgetDimension(max_tasks_per_day=3)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 1


def test_budget_cap_hook_allows_when_under_limit():
    dim = BudgetDimension(max_tasks_per_day=5)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_today=2)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is True


def test_budget_cap_hook_denies_when_at_limit():
    dim = BudgetDimension(max_tasks_per_day=3)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_today=3)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False
    assert "max_tasks_per_day" in decision.reason


def test_budget_cap_hook_denies_when_over_limit():
    dim = BudgetDimension(max_tasks_per_day=3)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_today=5)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False


def test_budget_dimension_validate_rejects_negative():
    dim = BudgetDimension(max_tasks_per_day=-1)
    with pytest.raises(ValueError, match="max_tasks_per_day"):
        dim.validate(MagicMock())


def test_budget_dimension_validate_accepts_zero():
    dim = BudgetDimension(max_tasks_per_day=0)
    dim.validate(MagicMock())  # must not raise
