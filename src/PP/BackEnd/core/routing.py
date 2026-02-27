"""
WAOOAW Router Factory — PP-N3b preventive gate.

Every route registered via waooaw_router() automatically inherits
platform-wide NFR gates. Add new cross-cutting concerns here once;
they apply to every PP route with no per-file changes.

DO NOT use bare APIRouter() in api/ directories.
Enforced by ruff lint rule in pyproject.toml.
"""

from fastapi import APIRouter, Depends
from core.dependencies import require_correlation_id


def waooaw_router(prefix: str = "", tags: list[str] | None = None, **kwargs) -> APIRouter:
    """Standard WAOOAW router with automatic NFR gate wiring.

    Every PP route registered here gets:
    - Correlation ID propagation (X-Correlation-ID header or auto-generated UUID)

    Future platform-wide gates added here apply to every PP route with no
    per-file changes needed.

    Args:
        prefix: URL prefix for all routes (e.g. "/agents").
        tags:   OpenAPI tag list (e.g. ["agents"]).
        **kwargs: Forwarded to APIRouter (responses, dependencies, etc.).

    Returns:
        APIRouter configured with WAOOAW NFR gates.
    """
    # Merge caller-provided dependencies with platform-level ones
    platform_deps = [Depends(require_correlation_id)]
    caller_deps = kwargs.pop("dependencies", [])
    return APIRouter(
        prefix=prefix,
        tags=tags or [],
        dependencies=platform_deps + caller_deps,
        **kwargs,
    )
