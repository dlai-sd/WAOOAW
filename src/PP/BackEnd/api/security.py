"""Security helpers for PP admin endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status

from core.config import Settings, get_settings


def _get_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def require_admin(
    request: Request,
    app_settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Require a valid PP-issued JWT with the `admin` role."""
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        claims = jwt.decode(
            token,
            app_settings.JWT_SECRET,
            algorithms=[app_settings.JWT_ALGORITHM],
            issuer=getattr(app_settings, "JWT_ISSUER", None) or None,
            options={"require": ["exp", "iat", "sub"], "verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return claims
