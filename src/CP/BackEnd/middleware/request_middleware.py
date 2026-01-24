from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Lightweight request middleware for CP BackEnd.

    Keeps behavior minimal so it won't break local/dev runs:
    - Adds a correlation id to request state/response header.
    - Passes through all requests without strict schema checks.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers.setdefault("x-correlation-id", correlation_id)
        return response
