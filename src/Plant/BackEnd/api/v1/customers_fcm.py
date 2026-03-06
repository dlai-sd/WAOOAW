"""FCM Push-token endpoint.

MOBILE-FUNC-1 S8a: Store or update the FCM push-notification device token for
the authenticated customer.

POST /api/v1/customers/fcm-token
  - Requires Bearer JWT (standard customer access token)
  - Reads customer_id from token claims (sub)
  - Stores token to customer_entity.fcm_token
  - Returns {"status": "ok"}
"""

from __future__ import annotations

from typing import Annotated, Any, Dict

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session              # write route — not read-replica
from core.routing import waooaw_router                # MANDATORY — never bare APIRouter
from core.security import verify_token
from core.exceptions import (
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
    BearerTokenMissingError,
)
from models.customer import Customer

router = waooaw_router(prefix="/customers", tags=["customers"])

logger = __import__("logging").getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def _require_customer_jwt(request: Request) -> Dict[str, Any]:
    """FastAPI dependency: validate Bearer JWT and return claims.

    Checks X-Original-Authorization (set by Plant Gateway) first, then
    falls back to the raw Authorization header.
    """
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    )
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Bearer token",
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token value",
        )
    try:
        claims = verify_token(token)
    except (JWTTokenExpiredError, JWTInvalidSignatureError, JWTInvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    return claims


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FcmTokenPayload(BaseModel):
    token: str


class FcmTokenResponse(BaseModel):
    status: str = "ok"


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/fcm-token", response_model=FcmTokenResponse, status_code=200)
async def store_fcm_token(
    payload: FcmTokenPayload,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    claims: Annotated[Dict[str, Any], Depends(_require_customer_jwt)],
) -> FcmTokenResponse:
    """Store or update the FCM push token for the authenticated customer.

    The token is written to ``customer_entity.fcm_token``.  Empty-string tokens
    are silently ignored so clients can call this endpoint defensively without
    crashing the login flow (fire-and-forget pattern).
    """
    token = (payload.token or "").strip()
    if not token:
        # Nothing to store — return success so callers don't need to pre-check.
        return FcmTokenResponse()

    customer_id = claims.get("sub")
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    customer.fcm_token = token
    await db.commit()

    logger.info("customers_fcm: stored FCM token for customer_id=%s", customer_id)
    return FcmTokenResponse()
