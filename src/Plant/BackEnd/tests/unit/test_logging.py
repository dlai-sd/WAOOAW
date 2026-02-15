"""Unit tests for core/logging.py."""

from __future__ import annotations

import json
import logging
import sys

import pytest

from core.logging import JSONFormatter, get_logger


@pytest.mark.unit
def test_get_logger_is_idempotent_for_same_name():
    logger1 = get_logger("plant.test.logger", level="INFO")
    logger2 = get_logger("plant.test.logger", level="INFO")
    assert logger1 is logger2


@pytest.mark.unit
def test_json_formatter_includes_exception_when_present():
    formatter = JSONFormatter()

    try:
        raise ValueError("boom")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="plant.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="something failed",
        args=(),
        exc_info=exc_info,
    )

    rendered = formatter.format(record)
    parsed = json.loads(rendered)

    assert parsed["level"] == "ERROR"
    assert parsed["message"] == "something failed"
    assert "exception" in parsed
