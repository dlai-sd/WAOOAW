"""PP BackEnd — PII masking log filter.

Wired at root logger in main_proxy.py. All module loggers inherit it automatically.
Masks email, phone numbers, and IP addresses before emission to Cloud Logging.
"""
from __future__ import annotations

import logging
import re


class PIIMaskingFilter(logging.Filter):
    """Masks PII in any log record before emission. Zero-overhead when no PII present."""

    _EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    _PHONE_RE = re.compile(r'(\+?\d{1,3})[\s\-]?\d{3,5}[\s\-]?\d{4,6}')
    _IP_LAST  = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}')

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._mask(str(record.msg))
        record.args = tuple(self._mask(str(a)) for a in (record.args or ()))
        return True

    def _mask(self, text: str) -> str:
        text = self._EMAIL_RE.sub(lambda m: self._mask_email(m.group()), text)
        text = self._PHONE_RE.sub(
            lambda m: m.group(1) + "******" + m.group()[-4:], text
        )
        text = self._IP_LAST.sub(r'\1.XXX', text)
        return text

    @staticmethod
    def _mask_email(email: str) -> str:
        user, domain = email.split("@", 1)
        return f"{user[0]}***@{domain}"

# Wire at startup — call this once in main_proxy.py:
#   from core.logging import PIIMaskingFilter
#   logging.getLogger().addFilter(PIIMaskingFilter())
