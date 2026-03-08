"""Unit tests for worker/tasks/component_tasks.py (EXEC-ENGINE-001 E3-S2).

Tests:
  E3-S2-T1: _run_component returns data dict when component safe_execute succeeds
  E3-S2-T2: _run_component calls task.retry when safe_execute returns success=False
  E3-S2-T3: celery_app.conf.task_routes contains pump/processor/publisher keys
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentOutput


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_run_component_success():
    """E3-S2-T1: _run_component returns data when safe_execute succeeds."""
    mock_comp = MagicMock()
    mock_comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=True, data={"ok": 1})
    )
    with patch("worker.tasks.component_tasks.get_component", return_value=mock_comp):
        from worker.tasks.component_tasks import _run_component  # noqa: PLC0415

        mock_task = MagicMock()
        result = _run_component(
            mock_task,
            "SomeComp",
            {
                "flow_run_id": "fr-1",
                "customer_id": "c-1",
                "skill_config": {},
                "run_context": {},
                "previous_step_output": None,
            },
            "fr-1",
        )
    assert result == {"ok": 1}


@pytest.mark.unit
def test_run_component_failure_calls_retry():
    """E3-S2-T2: _run_component calls task.retry when safe_execute returns failure."""
    mock_comp = MagicMock()
    mock_comp.safe_execute = AsyncMock(
        return_value=ComponentOutput(success=False, error_message="fail")
    )
    with patch("worker.tasks.component_tasks.get_component", return_value=mock_comp):
        from worker.tasks.component_tasks import _run_component  # noqa: PLC0415

        mock_task = MagicMock()
        mock_task.retry.side_effect = RuntimeError("retrying")
        with pytest.raises(RuntimeError, match="retrying"):
            _run_component(
                mock_task,
                "SomeComp",
                {
                    "flow_run_id": "fr-1",
                    "customer_id": "c-1",
                    "skill_config": {},
                    "run_context": {},
                    "previous_step_output": None,
                },
                "fr-1",
            )
    mock_task.retry.assert_called_once()


@pytest.mark.unit
def test_task_routes_contain_component_queues():
    """E3-S2-T3: celery_app.conf.task_routes has pump/processor/publisher."""
    from worker.celery_app import celery_app  # noqa: PLC0415

    routes = celery_app.conf.task_routes
    assert routes.get("execute_pump", {}).get("queue") == "pump"
    assert routes.get("execute_processor", {}).get("queue") == "processor"
    assert routes.get("execute_publisher", {}).get("queue") == "publisher"


@pytest.mark.unit
def test_execute_pump_task_is_registered():
    """execute_pump task is registered on celery_app."""
    # Import will also register the task on the app
    import worker.tasks.component_tasks  # noqa: F401
    from worker.celery_app import celery_app  # noqa: PLC0415

    assert "execute_pump" in celery_app.tasks


@pytest.mark.unit
def test_execute_processor_task_is_registered():
    """execute_processor task is registered on celery_app."""
    import worker.tasks.component_tasks  # noqa: F401
    from worker.celery_app import celery_app  # noqa: PLC0415

    assert "execute_processor" in celery_app.tasks


@pytest.mark.unit
def test_execute_publisher_task_is_registered():
    """execute_publisher task is registered on celery_app."""
    import worker.tasks.component_tasks  # noqa: F401
    from worker.celery_app import celery_app  # noqa: PLC0415

    assert "execute_publisher" in celery_app.tasks
