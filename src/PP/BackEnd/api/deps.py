"""Shared FastAPI dependencies for PP API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import Request


def get_authorization_header(request: Request) -> Optional[str]:
    """Return the incoming Authorization header (if present).

    PP backend acts as a thin proxy to Plant Gateway for many routes.
    Forwarding the caller's Bearer token avoids accidental unauthenticated
    calls upstream.
    """

    return request.headers.get("authorization")
