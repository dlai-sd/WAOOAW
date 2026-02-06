"""Exchange credential endpoints (PP).

Admin-only in Phase 1 (ops-assisted). These endpoints store raw keys encrypted
at rest and return opaque `exchange_account_id` values.

Plant should never receive raw keys from a browser request.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import require_admin
from services.exchange_credentials import (
    ExchangeCredential,
    FileExchangeCredentialStore,
    get_exchange_credential_store,
)


router = APIRouter(prefix="/exchange-credentials", tags=["exchange-credentials"])


class UpsertExchangeCredentialRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    exchange_provider: str = Field(..., min_length=1)

    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)

    exchange_account_id: Optional[str] = None


class ExchangeCredentialResponse(BaseModel):
    exchange_account_id: str
    customer_id: str
    exchange_provider: str
    created_at: str
    updated_at: str


class ExchangeCredentialBundleResponse(BaseModel):
    exchange_account_id: str
    exchange_provider: str
    api_key: str
    api_secret: str


def _to_response(model: ExchangeCredential) -> ExchangeCredentialResponse:
    return ExchangeCredentialResponse(
        exchange_account_id=model.exchange_account_id,
        customer_id=model.customer_id,
        exchange_provider=model.exchange_provider,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


@router.put("", response_model=ExchangeCredentialResponse)
async def upsert_exchange_credential(
    body: UpsertExchangeCredentialRequest,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileExchangeCredentialStore = Depends(get_exchange_credential_store),
) -> ExchangeCredentialResponse:
    saved = store.upsert(
        customer_id=body.customer_id,
        exchange_provider=body.exchange_provider,
        api_key=body.api_key,
        api_secret=body.api_secret,
        exchange_account_id=body.exchange_account_id,
    )
    return _to_response(saved)


class ExchangeCredentialListResponse(BaseModel):
    count: int
    credentials: List[Dict[str, Any]]


@router.get("", response_model=ExchangeCredentialListResponse)
async def list_exchange_credentials(
    customer_id: Optional[str] = None,
    limit: int = 100,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileExchangeCredentialStore = Depends(get_exchange_credential_store),
) -> ExchangeCredentialListResponse:
    rows = store.list(customer_id=customer_id, limit=limit)
    return ExchangeCredentialListResponse(count=len(rows), credentials=[_to_response(r).model_dump(mode="json") for r in rows])


@router.get("/{exchange_account_id}", response_model=ExchangeCredentialBundleResponse)
async def get_exchange_credential_bundle(
    exchange_account_id: str,
    _claims: Dict[str, Any] = Depends(require_admin),
    store: FileExchangeCredentialStore = Depends(get_exchange_credential_store),
) -> ExchangeCredentialBundleResponse:
    row = store.get(exchange_account_id=exchange_account_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Exchange account not found")

    return ExchangeCredentialBundleResponse(
        exchange_account_id=row.exchange_account_id,
        exchange_provider=row.exchange_provider,
        api_key=row.api_key,
        api_secret=row.api_secret,
    )
