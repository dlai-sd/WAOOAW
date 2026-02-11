"""Internal API for Plant to resolve platform credentials.

IMPORTANT: This endpoint must ONLY be accessible from Plant Backend (internal network).
Never expose this endpoint to browser/internet traffic.

Plant calls this endpoint to resolve credential_ref → actual secrets (access_token, refresh_token).
"""

from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from services.platform_credentials import (
    FilePlatformCredentialStore,
    get_platform_credential_store,
)


router = APIRouter(prefix="/internal/plant/credentials", tags=["internal-plant-credentials"])


class ResolveCredentialRequest(BaseModel):
    """Request to resolve a credential_ref for a customer."""
    customer_id: str
    credential_ref: str


class ResolveCredentialResponse(BaseModel):
    """Response with decrypted credential secrets."""
    credential_ref: str
    customer_id: str
    platform: str
    posting_identity: Optional[str] = None
    
    # Actual secrets (only returned to Plant)
    access_token: str
    refresh_token: Optional[str] = None
    
    # Metadata
    created_at: str
    updated_at: str


class UpdateTokenRequest(BaseModel):
    """Request to update access_token after OAuth2 refresh."""
    customer_id: str
    credential_ref: str
    new_access_token: str


def _verify_internal_request(x_plant_internal_key: str = Header(...)) -> None:
    """Verify request comes from Plant Backend (not browser traffic).
    
    In production, use proper service-to-service auth:
    - Mutual TLS
    - Service mesh (Istio)
    - Signed JWTs with short expiry
    
    For MVP/dev, simple shared secret.
    """
    import os
    expected_key = os.getenv("PLANT_INTERNAL_API_KEY", "dev-plant-internal-key")
    if x_plant_internal_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid internal API key")


@router.post("/resolve", response_model=ResolveCredentialResponse)
async def resolve_credential(
    body: ResolveCredentialRequest,
    store: FilePlatformCredentialStore = Depends(get_platform_credential_store),
    _: None = Depends(_verify_internal_request),
) -> ResolveCredentialResponse:
    """Resolve credential_ref to actual secrets for Plant to use.
    
    SECURITY: This endpoint MUST only be called by Plant Backend.
    """
    # Get encrypted secrets from store
    secrets = store.get_secrets(
        customer_id=body.customer_id,
        credential_ref=body.credential_ref,
    )
    
    if not secrets:
        raise HTTPException(
            status_code=404,
            detail=f"Credential not found: {body.credential_ref} for customer {body.customer_id}",
        )
    
    # Get credential metadata
    creds_list = store.list(customer_id=body.customer_id, limit=1000)
    cred = next((c for c in creds_list if c.credential_ref == body.credential_ref), None)
    
    if not cred:
        raise HTTPException(
            status_code=404,
            detail=f"Credential metadata not found: {body.credential_ref}",
        )
    
    # Return decrypted secrets to Plant
    return ResolveCredentialResponse(
        credential_ref=cred.credential_ref,
        customer_id=cred.customer_id,
        platform=cred.platform,
        posting_identity=cred.posting_identity,
        access_token=secrets.get("access_token", ""),
        refresh_token=secrets.get("refresh_token"),
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
    )


@router.post("/update-token", status_code=200)
async def update_access_token(
    body: UpdateTokenRequest,
    store: FilePlatformCredentialStore = Depends(get_platform_credential_store),
    _: None = Depends(_verify_internal_request),
) -> Dict[str, str]:
    """Update access_token after Plant refreshes it via OAuth2.
    
    SECURITY: This endpoint MUST only be called by Plant Backend.
    """
    # Get current secrets
    secrets = store.get_secrets(
        customer_id=body.customer_id,
        credential_ref=body.credential_ref,
    )
    
    if not secrets:
        raise HTTPException(
            status_code=404,
            detail=f"Credential not found: {body.credential_ref}",
        )
    
    # Update access_token, keep refresh_token unchanged
    secrets["access_token"] = body.new_access_token
    
    # Get credential metadata for upsert
    creds_list = store.list(customer_id=body.customer_id, limit=1000)
    cred = next((c for c in creds_list if c.credential_ref == body.credential_ref), None)
    
    if not cred:
        raise HTTPException(
            status_code=404,
            detail=f"Credential metadata not found: {body.credential_ref}",
        )
    
    # Upsert with updated token
    store.upsert(
        customer_id=body.customer_id,
        platform=cred.platform,
        posting_identity=cred.posting_identity,
        secrets_payload=secrets,
        metadata=cred.metadata,
        credential_ref=body.credential_ref,
    )
    
    return {"status": "success", "message": "Access token updated"}
