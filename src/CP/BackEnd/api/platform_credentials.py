"""CP platform credential routes.

Phase 2 grooming item: allow customers to connect platforms and store
credential references in CP.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.platform_credentials import (
    FilePlatformCredentialStore,
    PlatformCredentialPublic,
    get_platform_credential_store,
)


router = APIRouter(prefix="/cp/platform-credentials", tags=["cp-platform-credentials"])


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


class UpsertPlatformCredentialRequest(BaseModel):
    credential_ref: Optional[str] = None
    platform: str = Field(..., min_length=1)
    posting_identity: Optional[str] = None

    access_token: str = Field(..., min_length=1)
    refresh_token: Optional[str] = None


class PlatformCredentialResponse(PlatformCredentialPublic):
    pass


@router.put("", response_model=PlatformCredentialResponse)
async def upsert_platform_credential(
    body: UpsertPlatformCredentialRequest,
    current_user: User = Depends(get_current_user),
    store: FilePlatformCredentialStore = Depends(get_platform_credential_store),
) -> PlatformCredentialResponse:
    model = store.upsert(
        customer_id=_customer_id_from_user(current_user),
        platform=body.platform,
        posting_identity=body.posting_identity,
        secrets_payload={
            "access_token": body.access_token,
            "refresh_token": body.refresh_token,
        },
        metadata={},
        credential_ref=(body.credential_ref or None),
    )
    return PlatformCredentialResponse(**model.model_dump())


@router.get("", response_model=List[PlatformCredentialResponse])
async def list_platform_credentials(
    platform: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    store: FilePlatformCredentialStore = Depends(get_platform_credential_store),
) -> List[PlatformCredentialResponse]:
    rows = store.list(customer_id=_customer_id_from_user(current_user), platform=platform, limit=limit)
    return [PlatformCredentialResponse(**r.model_dump()) for r in rows]
