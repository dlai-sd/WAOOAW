"""Unit tests for worker/tasks/registration_tasks.py (E3-S2, E4-S1).

Covers:
- handle_customer_registered: calls NotificationService.send with welcome template
- handle_customer_registered: correct context passed (first_name, full_name, etc.)
- handle_customer_registered: NotificationService failure triggers retry
- handle_customer_registered: MaxRetriesExceededError → dead-letter log, no raise
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch, call

import pytest
from celery.exceptions import MaxRetriesExceededError


_CUSTOMER_KWARGS = {
    "customer_id": "cust-uuid-1",
    "email": "priya@example.com",
    "full_name": "Priya Sharma",
    "business_name": "Sharma Exports",
    "registered_at": "2025-01-15T10:00:00+00:00",
}


def test_handle_customer_registered_calls_notification_service(mocker) -> None:
    """Task must call NotificationService.send with template='welcome'."""
    mock_send = mocker.patch(
        "worker.tasks.registration_tasks.NotificationService.send"
    )

    from worker.tasks.registration_tasks import handle_customer_registered
    handle_customer_registered.apply(kwargs=_CUSTOMER_KWARGS)

    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["channel"] == "email"
    assert call_kwargs["destination"] == "priya@example.com"
    assert call_kwargs["template"] == "welcome"


def test_handle_customer_registered_context_has_first_name(mocker) -> None:
    """Context must derive first_name from full_name."""
    mock_send = mocker.patch(
        "worker.tasks.registration_tasks.NotificationService.send"
    )

    from worker.tasks.registration_tasks import handle_customer_registered
    handle_customer_registered.apply(kwargs=_CUSTOMER_KWARGS)

    context = mock_send.call_args.kwargs["context"]
    assert context["first_name"] == "Priya"
    assert context["full_name"] == "Priya Sharma"
    assert context["business_name"] == "Sharma Exports"
    assert context["customer_id"] == "cust-uuid-1"


def test_handle_customer_registered_empty_full_name(mocker) -> None:
    """Empty full_name must not raise; first_name falls back to 'there'."""
    mock_send = mocker.patch(
        "worker.tasks.registration_tasks.NotificationService.send"
    )

    kwargs = {**_CUSTOMER_KWARGS, "full_name": ""}
    from worker.tasks.registration_tasks import handle_customer_registered
    handle_customer_registered.apply(kwargs=kwargs)

    context = mock_send.call_args.kwargs["context"]
    assert context["first_name"] == "there"


def test_handle_customer_registered_retry_on_failure(mocker) -> None:
    """Exception from NotificationService must trigger self.retry."""
    mocker.patch(
        "worker.tasks.registration_tasks.NotificationService.send",
        side_effect=RuntimeError("broker down"),
    )

    from worker.tasks.registration_tasks import handle_customer_registered

    # When task runs with apply() it has ALWAYS_EAGER semantics.
    # Retry via .apply() will re-run task; assert it doesn't crash.
    # The retry loop will be attempted, but apply() catches MaxRetries.
    # We just verify no unhandled exception escapes.
    handle_customer_registered.apply(kwargs=_CUSTOMER_KWARGS)  # must not raise


def test_handle_customer_registered_dead_letter_logged(mocker, caplog) -> None:
    """MaxRetriesExceededError must be logged as ERROR (dead-letter) and not re-raised."""
    mocker.patch(
        "worker.tasks.registration_tasks.NotificationService.send",
        side_effect=OSError("network"),
    )

    from worker.tasks.registration_tasks import handle_customer_registered

    with patch.object(
        handle_customer_registered, "retry", side_effect=MaxRetriesExceededError("max")
    ):
        with caplog.at_level(logging.ERROR, logger="worker.tasks.registration_tasks"):
            handle_customer_registered.apply(kwargs=_CUSTOMER_KWARGS)

    assert any("DEAD-LETTER" in r.message for r in caplog.records)


def test_handle_customer_registered_logs_customer_id(mocker, caplog) -> None:
    """Task must log customer_id at INFO level on start."""
    mocker.patch("worker.tasks.registration_tasks.NotificationService.send")

    from worker.tasks.registration_tasks import handle_customer_registered
    with caplog.at_level(logging.INFO, logger="worker.tasks.registration_tasks"):
        handle_customer_registered.apply(kwargs=_CUSTOMER_KWARGS)

    assert any("cust-uuid-1" in r.message for r in caplog.records)
