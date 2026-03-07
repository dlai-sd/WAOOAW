# src/Plant/BackEnd/agent_mold/pump.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePump(ABC):
    """Every agent pump must inherit this ABC.

    Pump fetches data that the Processor will consume in the current goal run.
    Input: goal_config dict from agent_skills.goal_config JSONB.
    Output: any data object — must be serialisable.
    """

    @abstractmethod
    async def pull(self, *, goal_config: dict[str, Any], hired_agent_id: str) -> Any:
        """Fetch data for this execution cycle. Must be async."""
        ...

    @classmethod
    def pump_type(cls) -> str:
        return cls.__name__


class GoalConfigPump(BasePump):
    """Default pump: reads goal_config from DB. No external I/O."""

    async def pull(self, *, goal_config: dict[str, Any], hired_agent_id: str) -> dict[str, Any]:
        return goal_config
