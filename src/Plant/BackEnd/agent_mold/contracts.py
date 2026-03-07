"""Dimension contracts.

Chunk A provides a minimal contract interface plus safe NullDimension behavior.
Later chunks will add richer compile/materialize/enforcement logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from agent_mold.spec import AgentSpec, CompiledAgentSpec, DimensionName


@dataclass(frozen=True)
class DimensionContext:
    """Runtime context for dimension compilation/materialization.

    This is intentionally small initially; it will grow as we add:
    - customer profile
    - industry profile
    - integrations and credentials
    - AI Explorer routing
    """

    correlation_id: Optional[str] = None


class DimensionContract(ABC):
    """Interface implemented by all dimensions."""

    name: DimensionName
    version: str = "1.0"

    @abstractmethod
    def validate(self, spec: AgentSpec) -> None:
        """Validate the dimension configuration inside the AgentSpec."""

    @abstractmethod
    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        """Return dimension artifacts needed at runtime (schemas, adapters, templates)."""

    @abstractmethod
    def register_hooks(self, hook_bus: Any) -> None:
        """Register enforcement hooks (trial, budget, approvals)."""

    @abstractmethod
    def observe(self, event: Any) -> None:
        """Observe runtime events for learning/metrics."""


class NullDimension(DimensionContract):
    """Explicit null/void dimension implementation."""

    def __init__(self, name: DimensionName):
        self.name = name

    def validate(self, spec: AgentSpec) -> None:
        return None

    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        return {"present": False, "name": self.name}

    def register_hooks(self, hook_bus: Any) -> None:
        return None

    def observe(self, event: Any) -> None:
        return None


class BasicDimension(DimensionContract):
    """Minimal dimension implementation for compile/materialize.

    This is intentionally shallow: it provides a stable runtime bundle shape
    (present/name/config/version) without introducing full per-dimension
    behavior yet.
    """

    def __init__(self, name: DimensionName, *, version: str = "1.0"):
        self.name = name
        self.version = version

    def validate(self, spec: AgentSpec) -> None:
        # AgentSpec validation enforces config requirements; registry controls
        # which dimensions are required by agent type in later epics.
        return None

    def materialize(self, compiled: CompiledAgentSpec, context: DimensionContext) -> Dict[str, Any]:
        dim_spec = compiled.dimensions.get(self.name)
        if dim_spec is None:
            return {"present": False, "name": self.name, "version": self.version, "config": {}}

        if not dim_spec.present:
            return {"present": False, "name": self.name, "version": dim_spec.version, "config": {}}

        return {
            "present": True,
            "name": self.name,
            "version": dim_spec.version,
            "config": dict(dim_spec.config or {}),
        }

    def register_hooks(self, hook_bus: Any) -> None:
        return None

    def observe(self, event: Any) -> None:
        return None


@dataclass(frozen=True)
class RuntimeBundle:
    """Materialized runtime artifacts for an agent.

    The bundle is the product of: AgentSpec -> CompiledAgentSpec -> artifacts.
    """

    compiled: CompiledAgentSpec
    artifacts: Dict[DimensionName, Dict[str, Any]]


class TrialDimension(DimensionContract):
    """TRIAL dimension — enforces trial_task_limit at PRE_PUMP stage.

    Compiles into a QuotaGateHook registered on the HookBus.
    When tasks_used >= trial_task_limit the hook returns DENY and fires
    the on_quota_exhausted lifecycle event.

    trial_task_limit is read from AgentSpec.constraint_policy at register time.
    Default limit: 10 (matches ConstraintPolicy default).
    """

    name = DimensionName.TRIAL

    def __init__(self, *, trial_task_limit: int = 10):
        self.trial_task_limit = trial_task_limit

    def validate(self, spec: "AgentSpec") -> None:  # noqa: F821
        if self.trial_task_limit < 1:
            raise ValueError("trial_task_limit must be >= 1")

    def materialize(self, compiled: "CompiledAgentSpec", context: DimensionContext) -> Dict[str, Any]:
        return {
            "present": True,
            "name": self.name,
            "version": self.version,
            "trial_task_limit": self.trial_task_limit,
        }

    def register_hooks(self, hook_bus: Any) -> None:
        """Register QuotaGateHook at PRE_PUMP stage.

        HookBus is the live instance from GoalSchedulerService.
        The hook reads tasks_used from the goal_run context at fire time.
        """
        from agent_mold.hooks import HookStage

        trial_limit = self.trial_task_limit

        class _TrialQuotaHook:
            """Blocks execution if trial task limit is reached."""

            def __call__(self, event: Any) -> Any:
                from agent_mold.hooks import HookDecision
                tasks_used = getattr(event, "tasks_used", 0) or 0
                if tasks_used >= trial_limit:
                    return HookDecision(
                        proceed=False,
                        reason=f"trial_task_limit reached ({tasks_used}/{trial_limit})",
                        decision_id=f"trial-quota-deny-{tasks_used}",
                    )
                return HookDecision(proceed=True, reason="within_trial_quota", decision_id="trial-quota-allow")

        hook_bus.register(HookStage.PRE_PUMP, _TrialQuotaHook())

    def observe(self, event: Any) -> None:
        # Future: emit metric when quota_remaining drops below 20%
        pass


class BudgetDimension(DimensionContract):
    """BUDGET dimension — enforces max_tasks_per_day at PRE_PUMP stage.

    Compiles into a daily task cap hook registered on the HookBus.
    When tasks_today >= max_tasks_per_day (and max > 0), blocks execution.
    max_tasks_per_day=0 means no limit (unlimited).
    """

    name = DimensionName.BUDGET

    def __init__(self, *, max_tasks_per_day: int = 0):
        self.max_tasks_per_day = max_tasks_per_day  # 0 = no limit

    def validate(self, spec: "AgentSpec") -> None:  # noqa: F821
        if self.max_tasks_per_day < 0:
            raise ValueError("max_tasks_per_day cannot be negative")

    def materialize(self, compiled: "CompiledAgentSpec", context: DimensionContext) -> Dict[str, Any]:
        return {
            "present": True,
            "name": self.name,
            "version": self.version,
            "max_tasks_per_day": self.max_tasks_per_day,
        }

    def register_hooks(self, hook_bus: Any) -> None:
        """Register daily task cap hook at PRE_PUMP stage.

        Checks tasks_today from event context. Skipped when max_tasks_per_day=0.
        """
        from agent_mold.hooks import HookStage

        max_daily = self.max_tasks_per_day
        if max_daily == 0:
            return  # No limit configured — register nothing

        class _DailyTaskCapHook:
            """Blocks execution if today's task count reaches max_tasks_per_day."""

            def __call__(self, event: Any) -> Any:
                from agent_mold.hooks import HookDecision
                tasks_today = getattr(event, "tasks_today", 0) or 0
                if tasks_today >= max_daily:
                    return HookDecision(
                        proceed=False,
                        reason=f"max_tasks_per_day reached ({tasks_today}/{max_daily})",
                        decision_id=f"budget-cap-deny-{tasks_today}",
                    )
                return HookDecision(proceed=True, reason="within_daily_budget", decision_id="budget-cap-allow")

        hook_bus.register(HookStage.PRE_PUMP, _DailyTaskCapHook())

    def observe(self, event: Any) -> None:
        # Future: emit Prometheus counter when daily budget is 80% consumed
        pass
