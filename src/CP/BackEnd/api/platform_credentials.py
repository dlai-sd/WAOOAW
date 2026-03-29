"""CP platform credential routes.

Phase 2 grooming item: allow customers to connect platforms and store
credential references in CP.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.audit_dependency import AuditLogger, get_audit_logger
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError
from services.platform_credentials import (
    FilePlatformCredentialStore,
    PlatformCredentialPublic,
    get_platform_credential_store,
)

router = waooaw_router(prefix="/cp/platform-credentials", tags=["cp-platform-credentials"])

def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


def get_plant_gateway_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        headers["X-Correlation-ID"] = correlation
    return headers

class UpsertPlatformCredentialRequest(BaseModel):
    credential_ref: Optional[str] = None
    platform: str = Field(..., min_length=1)
    posting_identity: Optional[str] = None

    access_token: str = Field(..., min_length=1)
    refresh_token: Optional[str] = None

class PlatformCredentialResponse(PlatformCredentialPublic):
    pass


class ConnectYouTubeCredentialRefRequest(BaseModel):
    hired_instance_id: str = Field(..., min_length=1)
    skill_id: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)


@router.post("/youtube", response_model=Dict[str, Any], status_code=201)
async def connect_youtube_credential_ref(
    body: ConnectYouTubeCredentialRefRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/hired-agents/{body.hired_instance_id}/platform-connections",
            headers=_forward_headers(request),
            json_body={
                "skill_id": body.skill_id,
                "platform_key": "youtube",
                "secret_ref": body.credential_ref,
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    await audit.log(
        "cp_platform_credentials",
        "youtube_credential_ref_connected",
        "success",
        user_id=current_user.id,
        metadata={"hired_instance_id": body.hired_instance_id, "skill_id": body.skill_id},
    )
    return resp.json if isinstance(resp.json, dict) else {"status": "connected"}

@router.put("", response_model=PlatformCredentialResponse)
async def upsert_platform_credential(
    body: UpsertPlatformCredentialRequest,
    current_user: User = Depends(get_current_user),
    store: FilePlatformCredentialStore = Depends(get_platform_credential_store),
) -> PlatformCredentialResponse:
    model = await store.upsert(
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
    rows = await store.list(customer_id=_customer_id_from_user(current_user), platform=platform, limit=limit)
    return [PlatformCredentialResponse(**r.model_dump()) for r in rows]
