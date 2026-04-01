"""Brand voice API — CP-WIZ-1 E1-S1."""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from core.security import verify_token
from services.brand_voice_service import get_brand_voice, upsert_brand_voice
from services.customer_service import CustomerService

router = waooaw_router(prefix="/brand-voice", tags=["brand-voice"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


class BrandVoicePayload(BaseModel):
    tone_keywords: list[str] = Field(default_factory=list)
    vocabulary_preferences: list[str] = Field(default_factory=list)
    messaging_patterns: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)
    voice_description: str = ""


def _get_bearer_token(request: Request) -> str:
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    )
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    return parts[1].strip()


async def _resolve_customer_id(
    request: Request,
    db: AsyncSession,
) -> str:
    claims = verify_token(_get_bearer_token(request))
    customer_service = CustomerService(db)

    for candidate in (
        claims.get("sub"),
        claims.get("user_id"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            customer = await customer_service.get_by_id(candidate.strip())
            if customer is not None:
                return str(customer.id)

    email = claims.get("email")
    if isinstance(email, str) and email.strip():
        customer = await customer_service.get_by_email(email.strip().lower())
        if customer is not None:
            return str(customer.id)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Customer context not found",
    )


def _to_payload(model) -> BrandVoicePayload:
    return BrandVoicePayload(
        tone_keywords=list(model.tone_keywords or []),
        vocabulary_preferences=list(model.vocabulary_preferences or []),
        messaging_patterns=list(model.messaging_patterns or []),
        example_phrases=list(model.example_phrases or []),
        voice_description=str(model.voice_description or ""),
    )


@router.get("/me", response_model=BrandVoicePayload)
async def get_my_brand_voice(
    request: Request,
    db: AsyncSession = Depends(get_read_db_session),
) -> BrandVoicePayload:
    """Return the authenticated customer's brand voice."""
    customer_id = await _resolve_customer_id(request, db)
    voice = await get_brand_voice(customer_id, db)
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand voice not found")
    logger.info("Brand voice fetched for customer_id=%s", customer_id)
    return _to_payload(voice)


@router.put("/me", response_model=BrandVoicePayload)
async def put_my_brand_voice(
    payload: BrandVoicePayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> BrandVoicePayload:
    """Create or update the authenticated customer's brand voice."""
    customer_id = await _resolve_customer_id(request, db)
    voice = await upsert_brand_voice(customer_id, payload.model_dump(), db)
    await db.commit()
    await db.refresh(voice)
    logger.info("Brand voice upserted for customer_id=%s", customer_id)
    return _to_payload(voice)
