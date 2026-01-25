"""Legacy error handler module (deprecated).

This file exists only for backwards compatibility with older imports that
referenced `error_handler_old`. All functionality has moved to
`src.Plant.Gateway.middleware.error_handler`.

Keeping this module as a thin re-export prevents automation/linters from
failing if the file is touched.
"""

from __future__ import annotations

from src.Plant.Gateway.middleware.error_handler import (  # noqa: F401
    ErrorHandlingMiddleware,
    create_problem_details,
    setup_error_handlers,
)

__all__ = [
    "setup_error_handlers",
    "create_problem_details",
    "ErrorHandlingMiddleware",
]
