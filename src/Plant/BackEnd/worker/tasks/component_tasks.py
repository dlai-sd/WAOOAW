"""Celery component tasks — pump / processor / publisher queues (EXEC-ENGINE-001 E3-S2).

Three tasks, one per component queue, all delegating to _run_component():
  execute_pump      → queue: "pump"      (market data / data ingestion components)
  execute_processor → queue: "processor" (analytics / signal processing components)
  execute_publisher → queue: "publisher" (output / posting / trade execution components)

Retry policy:
  pump:      max 3 retries / 5s delay
  processor: max 3 retries / 10s delay
  publisher: max 3 retries / 15s delay

Usage:
    execute_pump.delay(
        component_type="DeltaExchangePump",
        input_dict={...},
        flow_run_id="fr-abc",
    )
"""
from __future__ import annotations

import asyncio

from worker.celery_app import celery_app
from components import ComponentInput, get_component


@celery_app.task(
    name="execute_pump",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def execute_pump(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Celery task for pump-queue components (data ingestion)."""
    return _run_component(self, component_type, input_dict, flow_run_id)


@celery_app.task(
    name="execute_processor",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def execute_processor(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Celery task for processor-queue components (analytics / signal processing)."""
    return _run_component(self, component_type, input_dict, flow_run_id)


@celery_app.task(
    name="execute_publisher",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    acks_late=True,
)
def execute_publisher(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Celery task for publisher-queue components (output / posting)."""
    return _run_component(self, component_type, input_dict, flow_run_id)


def _run_component(task, component_type: str, input_dict: dict, flow_run_id: str) -> dict:  # noqa: ARG001
    """Look up component, run safe_execute(), retry on failure.

    Args:
        task:           Bound Celery task instance (for retry calls).
        component_type: Registry key for the component to run.
        input_dict:     Dict of ComponentInput field values.
        flow_run_id:    Parent FlowRun ID (used for logging / tracing).

    Returns:
        result.data dict if successful.

    Raises:
        celery.exceptions.Retry: on component failure (up to max_retries).
    """
    component = get_component(component_type)
    comp_input = ComponentInput(**input_dict)
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(component.safe_execute(comp_input))
    finally:
        loop.close()
    if not result.success:
        raise task.retry(exc=RuntimeError(result.error_message))
    return result.data
