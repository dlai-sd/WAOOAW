from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from core.security import verify_token
from services import redis_runtime

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/runtime/redis", tags=["runtime-redis"])


class RedisInvalidateRequest(BaseModel):
    namespace: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)


def _require_runtime_admin(request: Request) -> dict:
    auth = request.headers.get("X-Original-Authorization") or request.headers.get("Authorization") or ""
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    claims = verify_token(parts[1])
    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles and not claims.get("governor_agent_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return claims


@router.get("/health")
async def get_redis_health():
    try:
        return await redis_runtime.health_check()
    except Exception as exc:  # pragma: no cover - exercised via route tests
        logger.warning("runtime_redis.health failed: %s", exc)
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc


@router.get("/config")
async def get_redis_config():
    return redis_runtime.runtime_config()


@router.post("/invalidate")
async def invalidate_redis_key(
    payload: RedisInvalidateRequest,
    _: dict = Depends(_require_runtime_admin),
):
    try:
        return await redis_runtime.invalidate(payload.namespace, payload.key)
    except Exception as exc:  # pragma: no cover - exercised via route tests
        logger.warning("runtime_redis.invalidate failed: %s", exc)
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc
