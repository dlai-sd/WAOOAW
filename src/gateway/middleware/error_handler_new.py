"""Compatibility shim for GW-105 error handling.

`src.gateway.middleware.error_handler_new` was introduced during an
iteration but the canonical implementation lives in
`src.gateway.middleware.error_handler`.

This module re-exports the stable symbols so any legacy imports keep
working.
"""

from .error_handler import create_problem_details, setup_error_handlers

__all__ = ["setup_error_handlers", "create_problem_details"]
