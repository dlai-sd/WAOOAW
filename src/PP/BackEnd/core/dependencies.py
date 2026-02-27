"""
Global FastAPI dependencies — wired via app-level dependencies=[...].

Every request to PP BackEnd automatically runs these before reaching any route.
"""

import uuid
from contextvars import ContextVar
from fastapi import Request

# P-2: Correlation ID context var — available to log formatters and outbound
# httpx calls without thread-local gymnastics.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def require_correlation_id(request: Request) -> str:
    """Read X-Correlation-ID header or generate one; store in ContextVar.

    Returns:
        str: The correlation ID for this request.
    """
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    _correlation_id.set(cid)
    return cid
