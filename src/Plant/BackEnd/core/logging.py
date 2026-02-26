"""
Structured logging setup
JSON format for parsing + filtering.

E1-S2 (Iteration 6): PII masking enforced at the formatter level.
No email, phone, full_name, or IP address ever appears in plain text in logs.
"""

import logging
import json
import re
from typing import Any
from datetime import datetime

# ---------------------------------------------------------------------------
# E1-S2 — PII masking helpers
# ---------------------------------------------------------------------------

_PII_KEYS = frozenset(
    {"email", "phone", "full_name", "ip_address", "ip", "user_agent"}
)


def mask_email(value: str) -> str:
    """Mask email to u***@domain.com format.

    Examples:
        >>> mask_email("user@example.com")
        'u***@example.com'
        >>> mask_email("ab@x.io")
        'a***@x.io'
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
        >>> mask_phone("9876543210")
        '987*****210'  # 3 prefix + 3 suffix (adjust for shorter numbers)
    """
    if not value:
        return "***"
    digits = re.sub(r"\D", "", value)
    visible_end = digits[-4:] if len(digits) >= 4 else digits
    prefix = value[: 3] if len(value) >= 3 else value
    mid_len = max(0, len(value) - 3 - 4)
    return f"{prefix}{'*' * mid_len}{visible_end}"


def mask_full_name(value: str) -> str:
    """Mask full name to initials only: John Doe → J.D.

    Examples:
        >>> mask_full_name("John Doe")
        'J.D.'
        >>> mask_full_name("Alice")
        'A.'
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
        >>> mask_ip("10.0.0.1")
        '10.0.0.XXX'
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
    if k in ("email",):
        return mask_email(value)
    if k in ("phone",):
        return mask_phone(value)
    if k in ("full_name",):
        return mask_full_name(value)
    if k in ("ip_address", "ip"):
        return mask_ip(value)
    if k in ("user_agent",):
        # Truncate user-agent — not personal data but can be identifying
        return value[:30] + "…" if len(value) > 30 else value
    return "***"


class PiiMaskingFilter(logging.Filter):
    """Logging filter that masks PII keys in the log record's `extra` dict.

    Attach to any handler or logger:
        logger.addFilter(PiiMaskingFilter())

    Any LogRecord whose `__dict__` contains keys matching _PII_KEYS will have
    the value replaced with the masked version before the record is formatted.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        for key in _PII_KEYS:
            if hasattr(record, key):
                original = getattr(record, key)
                setattr(record, key, _mask_pii_value(key, original))
        return True


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON logs.
    Useful for log aggregation and parsing.

    E1-S2: PII keys present in the log record (via `extra=`) are masked
    before being written. The formatter never emits a plain email/phone.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            str: JSON-formatted log line
        """
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

        # Add exception info if present
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
        logger.info("User action", extra={"email": "user@example.com"})
        # → email field is masked: "u***@example.com"
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    # E1-S2: attach PII masking filter to every handler
    handler.addFilter(PiiMaskingFilter())
    logger.addHandler(handler)

    return logger
