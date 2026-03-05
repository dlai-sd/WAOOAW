"""Tests for PP BackEnd PII masking log filter (E3-S1)."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.unit
def test_pii_masking_filter_masks_email():
    """E3-S1-T1: Email addresses are masked in log records."""
    from core.logging import PIIMaskingFilter

    f = PIIMaskingFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="admin@waooaw.com logged in", args=(), exc_info=None,
    )
    result = f.filter(record)
    assert result is True
    assert record.msg == "a***@waooaw.com logged in"


@pytest.mark.unit
def test_pii_masking_filter_masks_ip_last_octet():
    """E3-S1-T2: The last octet of IP addresses is masked in log records."""
    from core.logging import PIIMaskingFilter

    f = PIIMaskingFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="IP 192.168.1.145 access", args=(), exc_info=None,
    )
    f.filter(record)
    assert record.msg == "IP 192.168.1.XXX access"
