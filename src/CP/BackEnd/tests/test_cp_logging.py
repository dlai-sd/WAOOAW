"""Unit tests for E1-S2 — PII masking in CP backend core.logging.

Ensures the CP logging module has identical masking contracts to Plant's.
"""

import json
import logging
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.logging import (
    JSONFormatter,
    PiiMaskingFilter,
    mask_email,
    mask_full_name,
    mask_ip,
    mask_phone,
    get_logger,
)


class TestCPMaskEmail:
    def test_standard(self):
        assert mask_email("cp_user@example.com") == "c***@example.com"

    def test_single_local_char(self):
        assert mask_email("a@b.io") == "a***@b.io"

    def test_no_at_sign(self):
        assert mask_email("invalid") == "***"

    def test_empty(self):
        assert mask_email("") == "***"


class TestCPMaskPhone:
    def test_e164(self):
        result = mask_phone("+919876543210")
        assert result.startswith("+91")
        assert result.endswith("3210")

    def test_empty(self):
        assert mask_phone("") == "***"


class TestCPMaskFullName:
    def test_two_words(self):
        assert mask_full_name("Priya Sharma") == "P.S."

    def test_single_word(self):
        assert mask_full_name("Om") == "O."

    def test_empty(self):
        assert mask_full_name("") == "***"


class TestCPMaskIp:
    def test_ipv4(self):
        assert mask_ip("10.0.0.1") == "10.0.0.XXX"

    def test_empty(self):
        assert mask_ip("") == "***"


class TestCPPiiMaskingFilter:
    def _make_record(self, **kwargs):
        record = logging.LogRecord(
            name="cp_test", level=logging.INFO,
            pathname="", lineno=0, msg="test",
            args=(), exc_info=None,
        )
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def test_email_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(email="cpuser@company.com")
        f.filter(record)
        assert record.email == "c***@company.com"

    def test_phone_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(phone="+918765432100")
        f.filter(record)
        assert "****" in record.phone

    def test_filter_always_true(self):
        f = PiiMaskingFilter()
        record = self._make_record()
        assert f.filter(record) is True

    def test_non_pii_untouched(self):
        f = PiiMaskingFilter()
        record = self._make_record(event_type="login")
        f.filter(record)
        assert record.event_type == "login"


class TestCPJSONFormatter:
    def test_masked_email_in_output(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="cp_test", level=logging.INFO,
            pathname="", lineno=0, msg="login",
            args=(), exc_info=None,
        )
        record.email = "cpuser@domain.com"
        output = json.loads(formatter.format(record))
        assert output["email"] != "cpuser@domain.com"
        assert output["email"] == "c***@domain.com"

    def test_no_pii_no_extra_keys(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="cp_test", level=logging.INFO,
            pathname="", lineno=0, msg="plain",
            args=(), exc_info=None,
        )
        output = json.loads(formatter.format(record))
        assert "email" not in output
        assert "phone" not in output


class TestCPGetLogger:
    def test_has_pii_filter(self):
        logger = get_logger("cp.test.filter_check")
        handlers_with_filter = [
            h for h in logger.handlers
            if any(isinstance(f, PiiMaskingFilter) for f in h.filters)
        ]
        assert len(handlers_with_filter) >= 1
