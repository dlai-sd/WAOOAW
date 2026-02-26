"""
Structured logging setup for CP backend.
JSON format for parsing + filtering.

E1-S2 (Iteration 6): PII masking enforced at the formatter level.
Mirrors src/Plant/BackEnd/core/logging.py — keep in sync.
"""

import logging
import json
import re
from typing import Any
from datetime import datetime

# ---------------------------------------------------------------------------
# E1-S2 — PII masking helpers (identical contract to Plant's core.logging)
# ---------------------------------------------------------------------------

_PII_KEYS = frozenset(
    {"email", "phone", "full_name", "ip_address", "ip", "user_agent"}
)


def mask_email(value: str) -> str:
    """Mask email to u***@domain.com format.

    Examples:
        >>> mask_email("user@example.com")
        'u***@example.com'
    """
    if not value or "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    return f"{local[0]}***@{domain}"


def mask_phone(value: str) -> str:
    """Mask phone number: keep first 3 chars + last 4 digits, mask the rest.

    Examples:
        >>> mask_phone("+919876543210")
        '+91*****3210'
    """
    if not value:
        return "***"
    digits = re.sub(r"\D", "", value)
    visible_end = digits[-4:] if len(digits) >= 4 else digits
    prefix = value[:3] if len(value) >= 3 else value
    mid_len = max(0, len(value) - 3 - 4)
    return f"{prefix}{'*' * mid_len}{visible_end}"


def mask_full_name(value: str) -> str:
    """Mask full name to initials only: John Doe → J.D.

    Examples:
        >>> mask_full_name("John Doe")
        'J.D.'
    """
    if not value:
        return "***"
    parts = value.split()
    return "".join(f"{p[0].upper()}." for p in parts if p)


def mask_ip(value: str) -> str:
    """Mask last octet of IPv4: 192.168.1.42 → 192.168.1.XXX.

    Examples:
        >>> mask_ip("192.168.1.42")
        '192.168.1.XXX'
    """
    if not value:
        return "***"
    parts = value.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".XXX"
    return "***"


def _mask_pii_value(key: str, value: Any) -> Any:
    """Return masked version of a PII value based on its key."""
    if not isinstance(value, str):
        return "***"
    k = key.lower()
    if k == "email":
        return mask_email(value)
    if k == "phone":
        return mask_phone(value)
    if k == "full_name":
        return mask_full_name(value)
    if k in ("ip_address", "ip"):
        return mask_ip(value)
    if k == "user_agent":
        return value[:30] + "…" if len(value) > 30 else value
    return "***"


class PiiMaskingFilter(logging.Filter):
    """Logging filter that masks PII keys in log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        for key in _PII_KEYS:
            if hasattr(record, key):
                original = getattr(record, key)
                setattr(record, key, _mask_pii_value(key, original))
        return True


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON logs.
    E1-S2: masks any PII keys present on the log record.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # E1-S2: include masked PII keys if present on the record
        for key in _PII_KEYS:
            if hasattr(record, key):
                log_data[key] = _mask_pii_value(key, getattr(record, key))

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (INFO, DEBUG, WARNING, ERROR)

    Returns:
        logging.Logger: Configured logger

    Example:
        logger = get_logger(__name__)
        logger.info("Registration", extra={"email": "user@example.com"})
        # → email field is masked: "u***@example.com"
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    handler.addFilter(PiiMaskingFilter())
    logger.addHandler(handler)

    return logger
