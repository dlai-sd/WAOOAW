"""Brand voice API — CP-WIZ-1 E1-S1."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from core.security import verify_token
from services.brand_voice_service import get_brand_voice, upsert_brand_voice

router = waooaw_router(prefix="/brand-voice", tags=["brand-voice"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


class BrandVoicePayload(BaseModel):
    """Brand voice fields exposed to customers."""

    tone_keywords: list[str] = Field(default_factory=list)
    vocabulary_preferences: list[str] = Field(default_factory=list)
    messaging_patterns: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)
    voice_description: str = ""

    model_config = ConfigDict(from_attributes=True, strict=True)


def _customer_id_from_request(request: Request) -> str:
    """Resolve customer identity from the forwarded JWT context."""
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    ).strip()
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        claims: dict[str, Any] | None = verify_token(parts[1].strip())
    except Exception as exc:  # pragma: no cover - core verifier behavior is covered elsewhere
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    token_type = str((claims or {}).get("token_type") or "access").strip().lower()
    if token_type not in {"", "access"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    customer_id = str(
        (claims or {}).get("customer_id")
        or (claims or {}).get("user_id")
        or (claims or {}).get("sub")
        or ""
    ).strip()
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing customer context",
        )
    return customer_id


@router.get("/me", response_model=BrandVoicePayload)
async def read_brand_voice(
    request: Request,
    db: AsyncSession = Depends(get_read_db_session),
) -> BrandVoicePayload:
    """Return the authenticated customer's brand voice."""
    customer_id = _customer_id_from_request(request)
    voice = await get_brand_voice(customer_id, db)
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand voice not found")
    logger.info("Brand voice fetched for customer_id=%s", customer_id)
    return BrandVoicePayload.model_validate(voice)


@router.put("/me", response_model=BrandVoicePayload)
async def write_brand_voice(
    request: Request,
    payload: BrandVoicePayload,
    db: AsyncSession = Depends(get_db_session),
) -> BrandVoicePayload:
    """Create or update the authenticated customer's brand voice."""
    customer_id = _customer_id_from_request(request)
    voice = await upsert_brand_voice(customer_id, payload.model_dump(), db)
    await db.commit()
    logger.info("Brand voice upserted for customer_id=%s", customer_id)
    return BrandVoicePayload.model_validate(voice)
