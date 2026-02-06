"""Metering debug routes.

These endpoints are intended for *local development only* to help operators mint
trusted metering envelope headers for manual testing.

Security posture:
- Disabled by default.
- Returns 404 unless ENABLE_METERING_DEBUG=true (or 1/yes)
- Returns 404 in prod-like environments.
"""

from __future__ import annotations

import base64
import hmac
import os
import time
from hashlib import sha256
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/metering-debug", tags=["metering-debug"])


def _is_enabled() -> bool:
    enabled = os.getenv("ENABLE_METERING_DEBUG", "false").lower() in {"1", "true", "yes"}
    env = os.getenv("ENVIRONMENT", "development").lower()
    prod_like = env in {"prod", "production", "uat"}
    return enabled and not prod_like


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


class MintEnvelopeRequest(BaseModel):
    correlation_id: str = Field(..., min_length=1)
    tokens_in: int = Field(0, ge=0)
    tokens_out: int = Field(0, ge=0)
    model: str = Field("")
    cache_hit: bool = Field(False)
    cost_usd: float = Field(0.0, ge=0.0)
    timestamp: Optional[int] = Field(None, description="Unix seconds; defaults to now")


class MintEnvelopeResponse(BaseModel):
    headers: Dict[str, str]


@router.post("/envelope", response_model=MintEnvelopeResponse)
async def mint_metering_envelope(body: MintEnvelopeRequest) -> MintEnvelopeResponse:
    """Mint trusted metering envelope headers for manual testing.

    This implements the canonical string contract documented in Plant:
    ts|correlation_id|tokens_in|tokens_out|model|cache_hit|cost_usd
    """

    if not _is_enabled():
        raise HTTPException(status_code=404, detail="Not Found")

    secret = os.getenv("METERING_ENVELOPE_SECRET")
    if not secret:
        raise HTTPException(status_code=400, detail="METERING_ENVELOPE_SECRET is not set")

    ts = int(body.timestamp or time.time())
    cache_hit = "1" if body.cache_hit else "0"
    cost_usd = f"{float(body.cost_usd):.6f}"

    canonical = f"{ts}|{body.correlation_id}|{body.tokens_in}|{body.tokens_out}|{body.model}|{cache_hit}|{cost_usd}"
    digest = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), sha256).digest()
    signature = _base64url(digest)

    headers = {
        "X-Metering-Timestamp": str(ts),
        "X-Metering-Tokens-In": str(body.tokens_in),
        "X-Metering-Tokens-Out": str(body.tokens_out),
        "X-Metering-Model": body.model,
        "X-Metering-Cache-Hit": cache_hit,
        "X-Metering-Cost-USD": cost_usd,
        "X-Metering-Signature": signature,
    }

    return MintEnvelopeResponse(headers=headers)
