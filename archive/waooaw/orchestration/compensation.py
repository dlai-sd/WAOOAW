"""
Compensation and Saga Pattern

Implements saga pattern for distributed transactions with compensation
handlers for rollback on failure.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from waooaw.common.logging_framework import StructuredLogger


class SagaState(Enum):
    """Saga execution states"""

    PENDING = "pending"  # Not started
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # All steps completed
    COMPENSATING = "compensating"  # Rolling back
    COMPENSATED = "compensated"  # Fully rolled back
    FAILED = "failed"  # Failed without full compensation


class CompensationError(Exception):
    """Raised when compensation handler fails"""

    pass


@dataclass
class SagaStep:
    """
    Single step in a saga transaction
    
    Each step has a forward action and compensation action for rollback.
    """

    name: str
    action: Callable  # Forward action (async callable)
    compensation: Optional[Callable] = None  # Rollback action (async callable)
    completed: bool = False
    compensated: bool = False
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

    async def execute(self) -> Any:
        """Execute forward action"""
        if asyncio.iscoroutinefunction(self.action):
            self.result = await self.action()
        else:
            self.result = self.action()

        self.completed = True
        return self.result

    async def compensate(self) -> None:
        """Execute compensation action"""
        if self.compensation is None:
            # No compensation needed
            self.compensated = True
            return

        if asyncio.iscoroutinefunction(self.compensation):
            await self.compensation(self.result)
        else:
            self.compensation(self.result)

        self.compensated = True


@dataclass
class SagaExecution:
    """
    Record of saga execution with all steps and their results
    """

    saga_id: str
    state: SagaState
    steps: List[SagaStep]
    completed_steps: int = 0
    compensated_steps: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_execution_time: float = 0.0
    error: Optional[str] = None

    @property
    def total_steps(self) -> int:
        """Total number of steps in saga"""
        return len(self.steps)

    @property
    def is_terminal(self) -> bool:
        """Check if saga is in terminal state"""
        return self.state in {
            SagaState.COMPLETED,
            SagaState.COMPENSATED,
            SagaState.FAILED,
        }


class Saga:
    """
    Saga coordinator for distributed transactions
    
    Implements the saga pattern where each operation has a corresponding
    compensation action to undo it in case of failure.
    
    Forward recovery: Try to complete all steps
    Backward recovery: Compensate completed steps in reverse order
    """

    def __init__(self, saga_id: str):
        """
        Initialize saga
        
        Args:
            saga_id: Unique saga identifier
        """
        self.saga_id = saga_id
        self._steps: List[SagaStep] = []
        self._state = SagaState.PENDING
        self._logger = StructuredLogger(name=f"saga-{saga_id}", level="INFO")

    def add_step(
        self,
        name: str,
        action: Callable,
        compensation: Optional[Callable] = None,
    ) -> "Saga":
        """
        Add step to saga
        
        Args:
            name: Step identifier
            action: Forward action (async callable)
            compensation: Compensation action (async callable)
            
        Returns:
            Self for chaining
        """
        step = SagaStep(name=name, action=action, compensation=compensation)
        self._steps.append(step)

        self._logger.info(
            "saga_step_added",
            extra={
                "saga_id": self.saga_id,
                "step_name": name,
                "has_compensation": compensation is not None,
                "total_steps": len(self._steps),
            },
        )

        return self

    async def execute(self) -> SagaExecution:
        """
        Execute saga with all steps
        
        Attempts to execute all steps in order. If any step fails,
        executes compensation for all completed steps in reverse order.
        
        Returns:
            SagaExecution record with results
        """
        execution = SagaExecution(
            saga_id=self.saga_id,
            state=SagaState.RUNNING,
            steps=self._steps,
            started_at=datetime.utcnow(),
        )

        self._state = SagaState.RUNNING

        self._logger.info(
            "saga_execution_started",
            extra={
                "saga_id": self.saga_id,
                "total_steps": len(self._steps),
            },
        )

        try:
            # Execute all steps in order
            for step in self._steps:
                start_time = datetime.utcnow()

                try:
                    self._logger.info(
                        "saga_step_executing",
                        extra={
                            "saga_id": self.saga_id,
                            "step_name": step.name,
                            "step_index": execution.completed_steps,
                        },
                    )

                    await step.execute()

                    step.execution_time = (
                        datetime.utcnow() - start_time
                    ).total_seconds()
                    execution.completed_steps += 1

                    self._logger.info(
                        "saga_step_completed",
                        extra={
                            "saga_id": self.saga_id,
                            "step_name": step.name,
                            "execution_time": step.execution_time,
                        },
                    )

                except Exception as error:
                    # Step failed - initiate compensation
                    step.error = str(error)
                    execution.error = f"Step '{step.name}' failed: {error}"

                    self._logger.error(
                        "saga_step_failed",
                        extra={
                            "saga_id": self.saga_id,
                            "step_name": step.name,
                            "error": str(error),
                            "completed_steps": execution.completed_steps,
                        },
                    )

                    # Compensate all completed steps
                    await self._compensate(execution)

                    return execution

            # All steps completed successfully
            execution.state = SagaState.COMPLETED
            self._state = SagaState.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.total_execution_time = (
                execution.completed_at - execution.started_at
            ).total_seconds()

            self._logger.info(
                "saga_execution_completed",
                extra={
                    "saga_id": self.saga_id,
                    "total_steps": execution.completed_steps,
                    "total_time": execution.total_execution_time,
                },
            )

            return execution

        except Exception as error:
            # Unexpected error during saga execution
            execution.state = SagaState.FAILED
            execution.error = f"Saga failed: {error}"
            execution.completed_at = datetime.utcnow()

            self._logger.error(
                "saga_execution_failed",
                extra={
                    "saga_id": self.saga_id,
                    "error": str(error),
                },
            )

            raise

    async def _compensate(self, execution: SagaExecution) -> None:
        """
        Execute compensation for all completed steps in reverse order
        
        Args:
            execution: Saga execution record to update
        """
        execution.state = SagaState.COMPENSATING
        self._state = SagaState.COMPENSATING

        self._logger.info(
            "saga_compensation_started",
            extra={
                "saga_id": self.saga_id,
                "steps_to_compensate": execution.completed_steps,
            },
        )

        # Compensate in reverse order
        completed_steps = [s for s in self._steps if s.completed]
        for step in reversed(completed_steps):
            try:
                self._logger.info(
                    "saga_step_compensating",
                    extra={
                        "saga_id": self.saga_id,
                        "step_name": step.name,
                    },
                )

                await step.compensate()
                execution.compensated_steps += 1

                self._logger.info(
                    "saga_step_compensated",
                    extra={
                        "saga_id": self.saga_id,
                        "step_name": step.name,
                    },
                )

            except Exception as error:
                # Compensation failed - critical error
                step.error = f"Compensation failed: {error}"
                execution.state = SagaState.FAILED
                self._state = SagaState.FAILED

                self._logger.error(
                    "saga_compensation_failed",
                    extra={
                        "saga_id": self.saga_id,
                        "step_name": step.name,
                        "error": str(error),
                    },
                )

                raise CompensationError(
                    f"Compensation failed for step '{step.name}': {error}"
                )

        # All compensations successful
        execution.state = SagaState.COMPENSATED
        self._state = SagaState.COMPENSATED
        execution.completed_at = datetime.utcnow()

        self._logger.info(
            "saga_compensation_completed",
            extra={
                "saga_id": self.saga_id,
                "compensated_steps": execution.compensated_steps,
            },
        )

    def get_state(self) -> SagaState:
        """Get current saga state"""
        return self._state

    def get_steps(self) -> List[SagaStep]:
        """Get all saga steps"""
        return self._steps.copy()


class SagaBuilder:
    """
    Builder for constructing sagas fluently
    
    Example:
        saga = (SagaBuilder("order-saga")
                .step("reserve-inventory", reserve, unreserve)
                .step("charge-payment", charge, refund)
                .step("ship-order", ship, cancel_shipment)
                .build())
    """

    def __init__(self, saga_id: str):
        """
        Initialize saga builder
        
        Args:
            saga_id: Unique saga identifier
        """
        self._saga = Saga(saga_id)

    def step(
        self,
        name: str,
        action: Callable,
        compensation: Optional[Callable] = None,
    ) -> "SagaBuilder":
        """
        Add step to saga
        
        Args:
            name: Step identifier
            action: Forward action
            compensation: Compensation action
            
        Returns:
            Self for chaining
        """
        self._saga.add_step(name, action, compensation)
        return self

    def build(self) -> Saga:
        """Build and return saga"""
        return self._saga
