"""
Common Components Module

Shared utilities for logging, config, secrets, health, metrics, etc.
Includes new Epic 5 components: cache, error_handler, state, security, resource_manager, validator.
"""
from waooaw.common.logging_framework import get_logger, configure_logging
from waooaw.common.config_manager import init_config, get_config
from waooaw.common.secrets_manager import init_secrets, get_secrets
from waooaw.common.health_checks import init_health, get_health, register_health_check
from waooaw.common.metrics import init_metrics, get_metrics
from waooaw.common.idempotency import init_idempotency, get_idempotency

# Epic 5: Common Components Library
from waooaw.common.cache import SimpleCache, CacheHierarchy
from waooaw.common.error_handler import (
    ErrorHandler,
    CircuitBreaker,
    RetryPolicy,
    DLQHandler,
    retry
)
from waooaw.common.state import StateManager, StateSnapshot
from waooaw.common.security import SecurityLayer, AuditLog, Permission
from waooaw.common.resource_manager import ResourceManager, Budget, RateLimitWindow
from waooaw.common.validator import (
    Validator,
    ValidationResult,
    DECISION_SCHEMA,
    ESCALATION_SCHEMA,
    GITHUB_ISSUE_SCHEMA
)

__all__ = [
    # Existing components
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
    
    # Epic 5: Cache
    "SimpleCache",
    "CacheHierarchy",
    
    # Epic 5: Error Handler
    "ErrorHandler",
    "CircuitBreaker",
    "RetryPolicy",
    "DLQHandler",
    "retry",
    
    # Epic 5: State Manager
    "StateManager",
    "StateSnapshot",
    
    # Epic 5: Security
    "SecurityLayer",
    "AuditLog",
    "Permission",
    
    # Epic 5: Resource Manager
    "ResourceManager",
    "Budget",
    "RateLimitWindow",
    
    # Epic 5: Validator
    "Validator",
    "ValidationResult",
    "DECISION_SCHEMA",
    "ESCALATION_SCHEMA",
    "GITHUB_ISSUE_SCHEMA",
]
