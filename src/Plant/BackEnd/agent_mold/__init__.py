"""Agent mold package.

This package contains the minimum building blocks to manufacture agents from
configuration (AgentSpec) while keeping dimension behavior explicit.

Chunk A deliverables: AgentSpec + DimensionContract + NullDimensions.
MOULD-GAP-1 additions: AgentLifecycleHooks + TrialDimension + BudgetDimension.
"""

from agent_mold.contracts import (
    DimensionContract,
    BasicDimension,
    NullDimension,
    TrialDimension,
    BudgetDimension,
)
from agent_mold.hooks import AgentLifecycleHooks, NullLifecycleHooks, LifecycleContext

__all__ = [
    "DimensionContract",
    "BasicDimension",
    "NullDimension",
    "TrialDimension",
    "BudgetDimension",
    "AgentLifecycleHooks",
    "NullLifecycleHooks",
    "LifecycleContext",
]
