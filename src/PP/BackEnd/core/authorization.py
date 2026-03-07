"""PP RBAC authorization — 7-role OPA hierarchy.

Provides ``require_role()`` factory that returns a FastAPI dependency
enforcing the minimum required role level based on JWT claims.

Usage::

    from core.authorization import require_role

    @router.get("/{id}/construct-health")
    async def get_construct_health(
        id: str,
        _auth = Depends(require_role("developer")),
    ):
        ...
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status

from core.config import Settings, get_settings
from core.logging import PIIMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

# 7-role OPA hierarchy (higher number = more privileged)
_ROLE_LEVEL: dict[str, int] = {
    "admin": 7,
    "developer": 6,
    "manager": 5,
    "agent_ops": 4,
    "support": 3,
    "readonly": 2,
    "viewer": 1,
}


def _get_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@lru_cache(maxsize=None)
def require_role(minimum_role: str) -> Callable:
    """Return a FastAPI dependency that enforces the minimum required PP role.

    Uses ``lru_cache`` so that identical ``minimum_role`` values return the
    same function object — this enables ``app.dependency_overrides`` to work
    correctly in tests.

    Role hierarchy (highest → lowest):
        admin > developer > manager > agent_ops > support > readonly > viewer

    Args:
        minimum_role: Minimum role name.  A token with ``admin`` satisfies
                      any minimum_role; a token with ``viewer`` only satisfies
                      ``viewer`` minimum.

    Returns:
        FastAPI-compatible dependency callable.
    """
    min_level = _ROLE_LEVEL.get(minimum_role, 0)

    def _dependency(
        request: Request,
        app_settings: Settings = Depends(get_settings),
    ) -> Dict[str, Any]:
        token = _get_bearer_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        claims = _decode_token(token, app_settings)
        roles = claims.get("roles") or []
        if isinstance(roles, str):
            roles = [roles]
        token_max_level = max((_ROLE_LEVEL.get(r, 0) for r in roles), default=0)
        if token_max_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Minimum role '{minimum_role}' required",
            )
        return claims

    return _dependency
