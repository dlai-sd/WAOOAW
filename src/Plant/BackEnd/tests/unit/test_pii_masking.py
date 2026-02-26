"""Unit tests for E1-S2 — PII masking in Plant core.logging.

Tests:
  - mask_email
  - mask_phone
  - mask_full_name
  - mask_ip
  - PiiMaskingFilter (via log records)
  - JSONFormatter masks PII fields in log output
"""

import json
import logging
import sys
import os

import pytest

# Add src to path for direct import in test container
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.logging import (
    JSONFormatter,
    PiiMaskingFilter,
    mask_email,
    mask_full_name,
    mask_ip,
    mask_phone,
    get_logger,
)


# ---------------------------------------------------------------------------
# mask_email
# ---------------------------------------------------------------------------


class TestMaskEmail:
    def test_standard_email(self):
        assert mask_email("user@example.com") == "u***@example.com"

    def test_single_char_local(self):
        assert mask_email("a@x.io") == "a***@x.io"

    def test_subdomain_preserved(self):
        result = mask_email("alice@mail.company.com")
        assert result.endswith("@mail.company.com")
        assert result.startswith("a***")

    def test_no_at_sign(self):
        assert mask_email("notanemail") == "***"

    def test_empty_string(self):
        assert mask_email("") == "***"

    def test_uppercase_email(self):
        result = mask_email("User@Example.com")
        assert result.startswith("U***@")


# ---------------------------------------------------------------------------
# mask_phone
# ---------------------------------------------------------------------------


class TestMaskPhone:
    def test_e164_indian_number(self):
        result = mask_phone("+919876543210")
        assert result.startswith("+91")
        assert result.endswith("3210")
        assert "****" in result

    def test_ten_digit_number(self):
        result = mask_phone("9876543210")
        assert result.startswith("987")
        assert result.endswith("3210")

    def test_empty_phone(self):
        assert mask_phone("") == "***"

    def test_short_number(self):
        # Should not crash on short numbers
        result = mask_phone("12")
        assert result is not None


# ---------------------------------------------------------------------------
# mask_full_name
# ---------------------------------------------------------------------------


class TestMaskFullName:
    def test_full_name_two_words(self):
        assert mask_full_name("John Doe") == "J.D."

    def test_single_word(self):
        assert mask_full_name("Alice") == "A."

    def test_three_words(self):
        assert mask_full_name("Mary Jane Watson") == "M.J.W."

    def test_empty_name(self):
        assert mask_full_name("") == "***"

    def test_lowercase(self):
        result = mask_full_name("john doe")
        assert result == "J.D."


# ---------------------------------------------------------------------------
# mask_ip
# ---------------------------------------------------------------------------


class TestMaskIp:
    def test_ipv4_standard(self):
        assert mask_ip("192.168.1.42") == "192.168.1.XXX"

    def test_all_zeros(self):
        assert mask_ip("0.0.0.0") == "0.0.0.XXX"

    def test_non_ipv4(self):
        # IPv6 or hostname — just returns ***
        assert mask_ip("::1") == "***"

    def test_empty(self):
        assert mask_ip("") == "***"


# ---------------------------------------------------------------------------
# PiiMaskingFilter
# ---------------------------------------------------------------------------


class TestPiiMaskingFilter:
    def _make_record(self, **kwargs):
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="test message",
            args=(), exc_info=None,
        )
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def test_email_is_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(email="test@example.com")
        f.filter(record)
        assert record.email == "t***@example.com"

    def test_phone_is_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(phone="+919876543210")
        f.filter(record)
        assert "****" in record.phone

    def test_full_name_is_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(full_name="John Doe")
        f.filter(record)
        assert record.full_name == "J.D."

    def test_ip_address_is_masked(self):
        f = PiiMaskingFilter()
        record = self._make_record(ip_address="10.0.0.1")
        f.filter(record)
        assert record.ip_address == "10.0.0.XXX"

    def test_non_pii_field_untouched(self):
        f = PiiMaskingFilter()
        record = self._make_record(customer_id="some-uuid-value")
        f.filter(record)
        assert record.customer_id == "some-uuid-value"

    def test_filter_returns_true(self):
        """filter() must always return True — never drop the record."""
        f = PiiMaskingFilter()
        record = self._make_record(email="x@y.com")
        result = f.filter(record)
        assert result is True


# ---------------------------------------------------------------------------
# JSONFormatter — PII keys in output
# ---------------------------------------------------------------------------


class TestJSONFormatterPiiMasking:
    def test_email_masked_in_json_output(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="registration",
            args=(), exc_info=None,
        )
        record.email = "user@domain.com"
        output = formatter.format(record)
        data = json.loads(output)
        assert "email" in data
        assert data["email"] != "user@domain.com"
        assert data["email"] == "u***@domain.com"

    def test_ip_masked_in_json_output(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="request",
            args=(), exc_info=None,
        )
        record.ip_address = "192.168.1.100"
        output = formatter.format(record)
        data = json.loads(output)
        assert data["ip_address"] == "192.168.1.XXX"

    def test_no_pii_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="plain log",
            args=(), exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        # No PII keys when not set
        assert "email" not in data
        assert "phone" not in data


# ---------------------------------------------------------------------------
# get_logger integration
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger_with_handler(self):
        logger = get_logger("test.pii_masking_test")
        assert logger is not None
        assert len(logger.handlers) >= 1

    def test_pii_filter_attached(self):
        logger = get_logger("test.pii_filter_check")
        handlers_with_filter = [
            h for h in logger.handlers
            if any(isinstance(f, PiiMaskingFilter) for f in h.filters)
        ]
        assert len(handlers_with_filter) >= 1
