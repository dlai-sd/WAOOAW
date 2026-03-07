# src/Plant/BackEnd/agent_mold/processor.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent_mold.hooks import HookBus


class ProcessorInput:
    """Typed base for all data flowing Pump → Processor."""

    def __init__(
        self,
        *,
        goal_config: dict[str, Any],
        raw_data: Any,
        correlation_id: str,
        hired_agent_id: str,
    ) -> None:
        self.goal_config = goal_config
        self.raw_data = raw_data
        self.correlation_id = correlation_id
        self.hired_agent_id = hired_agent_id


class ProcessorOutput:
    """Typed base for all data flowing Processor → Publisher."""

    def __init__(
        self,
        *,
        result: Any,
        metadata: dict[str, Any],
        correlation_id: str,
    ) -> None:
        self.result = result
        self.metadata = metadata
        self.correlation_id = correlation_id


class BaseProcessor(ABC):
    """Every agent processor must inherit this ABC.

    Plant BackEnd enforces: GoalSchedulerService calls process() expecting
    ProcessorInput and receiving ProcessorOutput — both types enforced at runtime.
    """

    @abstractmethod
    async def process(self, input_data: ProcessorInput, hook_bus: "HookBus") -> ProcessorOutput:
        """Execute agent-specific work. Must be async. Must return ProcessorOutput."""
        ...

    @classmethod
    def processor_type(cls) -> str:
        """Human-readable processor identifier for logs and metrics."""
        return cls.__name__
