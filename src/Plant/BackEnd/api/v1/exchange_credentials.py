"""Exchange credential routes for Share Trader (TRADER-FULL-1 S2 + S4)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from core.config import settings
from core.database import get_db_session, get_read_db_session
from core.datastore_router import datastore_router
from core.firestore_client import set_document
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from core.security import circuit_breaker
from services.exchange_credential_service import ExchangeCredentialService

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["exchange-credentials"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class UpsertExchangeCredentialRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    exchange_provider: str = Field(default="delta_exchange_india")
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    default_coin: str = Field(..., min_length=1)
    allowed_coins: List[str] = Field(default_factory=list)
    risk_limits: Dict[str, Any] = Field(default_factory=dict)


class ExchangeCredentialPublicResponse(BaseModel):
    credential_ref: str
    customer_id: str
    exchange_provider: str
    default_coin: str
    allowed_coins: List[str]
    risk_limits: Dict[str, Any]
    validation_status: str


class ValidateExchangeResponse(BaseModel):
    credential_ref: str
    readable: bool
    tradeable: bool
    balance_summary: Dict[str, Any]
    validation_status: str  # "valid" | "invalid"
    error: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/{hired_instance_id}/exchange-credentials",
    response_model=ExchangeCredentialPublicResponse,
    status_code=201,
)
async def upsert_exchange_credential(
    hired_instance_id: str,
    body: UpsertExchangeCredentialRequest,
    db=Depends(get_db_session),
) -> ExchangeCredentialPublicResponse:
    svc = ExchangeCredentialService(db)
    rec = await svc.upsert(
        customer_id=body.customer_id,
        exchange_provider=body.exchange_provider,
        api_key=body.api_key,       # svc encrypts internally
        api_secret=body.api_secret,  # svc encrypts internally
        default_coin=body.default_coin,
        allowed_coins=body.allowed_coins,
        risk_limits=body.risk_limits,
    )
    # Fire-and-forget dual-write to Firestore if DATA_ROUTER_MODE requires it
    if datastore_router.writes_to_firestore("exchange_credentials"):
        asyncio.create_task(
            set_document(
                "exchange_credentials",
                rec.credential_ref,
                {
                    "credential_ref": rec.credential_ref,
                    "customer_id": rec.customer_id,
                    "exchange_provider": rec.exchange_provider,
                    "default_coin": rec.default_coin,
                    "allowed_coins": rec.allowed_coins,
                    "validation_status": rec.validation_status,
                    # api_key and api_secret NEVER written to Firestore
                },
            )
        )
    return ExchangeCredentialPublicResponse(
        credential_ref=rec.credential_ref,
        customer_id=rec.customer_id,
        exchange_provider=rec.exchange_provider,
        default_coin=rec.default_coin,
        allowed_coins=rec.allowed_coins or [],
        risk_limits=rec.risk_limits or {},
        validation_status=rec.validation_status,
    )


@router.get(
    "/{hired_instance_id}/exchange-credentials",
    response_model=Optional[ExchangeCredentialPublicResponse],
)
async def get_exchange_credential(
    hired_instance_id: str,
    customer_id: str,
    db=Depends(get_read_db_session),  # GET uses read replica
) -> Optional[ExchangeCredentialPublicResponse]:
    svc = ExchangeCredentialService(db)
    rec = await svc.get_public(customer_id=customer_id)
    if rec is None:
        return None
    return ExchangeCredentialPublicResponse(
        credential_ref=rec.credential_ref,
        customer_id=rec.customer_id,
        exchange_provider=rec.exchange_provider,
        default_coin=rec.default_coin,
        allowed_coins=rec.allowed_coins or [],
        risk_limits=rec.risk_limits or {},
        validation_status=rec.validation_status,
    )


@router.post(
    "/{hired_instance_id}/exchange-credentials/{credential_ref}/validate",
    response_model=ValidateExchangeResponse,
)
async def validate_exchange_credential(
    hired_instance_id: str,
    credential_ref: str,
    db=Depends(get_db_session),
) -> ValidateExchangeResponse:
    svc = ExchangeCredentialService(db)
    secrets_dict = await svc.get_secrets(credential_ref=credential_ref)
    if secrets_dict is None:
        raise HTTPException(status_code=404, detail="credential_ref not found")

    readable, tradeable, balance_summary, error = await _validate_exchange_live(
        api_key=secrets_dict["api_key"],
        api_secret=secrets_dict["api_secret"],
    )
    status = "valid" if readable else "invalid"
    await svc.mark_validated(credential_ref=credential_ref, status=status)
    return ValidateExchangeResponse(
        credential_ref=credential_ref,
        readable=readable,
        tradeable=tradeable,
        balance_summary=balance_summary,
        validation_status=status,
        error=error,
    )


@circuit_breaker(service="delta_exchange_api")
async def _validate_exchange_live(
    *, api_key: str, api_secret: str, exchange_provider: str = "delta_exchange_india"
) -> tuple[bool, bool, dict, Optional[str]]:
    """Live Delta Exchange credential check. Returns (readable, tradeable, balance_summary, error).

    Mock is active in test/development/local unless DELTA_EXCHANGE_REAL_API=true.

    IMPORTANT — provider-specific base URL:
      delta_exchange_india  → https://api.india.delta.exchange
      delta_exchange        → https://api.delta.exchange
    These are SEPARATE platforms with separate accounts. India keys will return
    401 invalid_api_key on the international URL and vice versa.
    """
    import os
    env = settings.environment
    mock_envs = {"test", "development", "local"}
    force_real = os.environ.get("DELTA_EXCHANGE_REAL_API", "").lower() == "true"
    if env in mock_envs and not force_real:
        return True, True, {"mock": True, "available_balance": 100000}, None

    from integrations.delta_exchange.hmac_auth import build_auth_headers, base_url_for_provider
    base = base_url_for_provider(exchange_provider)
    balances_path = "/v2/wallet/balances"
    profile_path = "/v2/profile"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1 — verify read access (HMAC signed)
            balances_resp = await client.get(
                f"{base}{balances_path}",
                headers=build_auth_headers(
                    api_key=api_key, api_secret=api_secret,
                    method="GET", path=balances_path,
                ),
            )
            if balances_resp.status_code == 401:
                err_code = balances_resp.json().get("error", {}).get("code", "unknown")
                logger.error("validate_exchange: 401 from %s error_code=%s", base, err_code)
                return False, False, {}, (
                    f"Invalid credentials (code={err_code}). "
                    f"Ensure your key belongs to {exchange_provider} (→ {base})."
                )
            if balances_resp.status_code == 403:
                return False, False, {}, "API key lacks read permission"
            balances_resp.raise_for_status()
            balances = balances_resp.json().get("result", [])

            # Step 2 — verify the key is active
            profile_resp = await client.get(
                f"{base}{profile_path}",
                headers=build_auth_headers(
                    api_key=api_key, api_secret=api_secret,
                    method="GET", path=profile_path,
                ),
            )
            tradeable = profile_resp.status_code == 200
            return True, tradeable, {"balances_count": len(balances)}, None
    except Exception as exc:
        logger.error("validate_exchange: check failed — %s", type(exc).__name__)
        return False, False, {}, str(type(exc).__name__)
