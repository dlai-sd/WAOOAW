"""
Common Components Module

Shared utilities for logging, config, secrets, health, metrics, etc.
"""
from waooaw.common.logging_framework import get_logger, configure_logging
from waooaw.common.config_manager import init_config, get_config
from waooaw.common.secrets_manager import init_secrets, get_secrets
from waooaw.common.health_checks import init_health, get_health, register_health_check
from waooaw.common.metrics import init_metrics, get_metrics
from waooaw.common.idempotency import init_idempotency, get_idempotency

__all__ = [
    "get_logger",
    "configure_logging",
    "init_config",
    "get_config",
    "init_secrets",
    "get_secrets",
    "init_health",
    "get_health",
    "register_health_check",
    "init_metrics",
    "get_metrics",
    "init_idempotency",
    "get_idempotency",
]
