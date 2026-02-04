"""Security helpers for PP admin endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status

from core.config import Settings, get_settings


def _normalize_scopes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _decode_token(token: str, app_settings: Settings) -> Dict[str, Any]:
    try:
        return jwt.decode(
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

    claims = _decode_token(token, app_settings)

    # Scoped tokens are intentionally restricted and must not be used for
    # general admin routes.
    scopes = _normalize_scopes(claims.get("scope"))
    if scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Scoped token not permitted")

    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return claims


def require_db_updates_admin(
    request: Request,
    app_settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Require an admin token suitable for DB updates routes.

    Accepts either:
    - a standard admin access token (no scope claim)
    - a scoped token with scope == settings.DB_UPDATES_TOKEN_SCOPE
    """

    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    claims = _decode_token(token, app_settings)

    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    scopes = _normalize_scopes(claims.get("scope"))
    if not scopes:
        return claims

    allowed_scope = getattr(app_settings, "DB_UPDATES_TOKEN_SCOPE", "db_updates")
    if allowed_scope not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token scope")

    return claims
