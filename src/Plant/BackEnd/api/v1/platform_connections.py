"""Platform Connections API — PLANT-SKILLS-1 E4-S1

GET    /v1/hired-agents/{hired_instance_id}/platform-connections          — list connections
POST   /v1/hired-agents/{hired_instance_id}/platform-connections          — create connection
DELETE /v1/hired-agents/{hired_instance_id}/platform-connections/{conn_id} — delete connection
PATCH  /v1/hired-agents/{hired_instance_id}/platform-connections/{conn_id}/verify — set connected

CRITICAL: secret_ref is accepted on POST but NEVER returned in any GET response.
          secret_ref = GCP Secret Manager resource path only.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.customer_platform_credential import CustomerPlatformCredentialModel
from models.oauth_connection_session import OAuthConnectionSessionModel
from models.platform_connection import PlatformConnectionModel
from services.youtube_connection_service import YouTubeConnectionError, YouTubeConnectionService

router = waooaw_router(prefix="/hired-agents", tags=["platform-connections"])
customer_router = waooaw_router(prefix="/customer-platform-connections", tags=["customer-platform-connections"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CreateConnectionRequest(BaseModel):
    skill_id: str
    platform_key: str
    customer_platform_credential_id: Optional[str] = None
    # GCP Secret Manager resource path ONLY — never the raw secret value
    # e.g. "projects/waooaw-oauth/secrets/hired-abc123-delta-exchange/versions/latest"
    secret_ref: Optional[str] = None


class ConnectionResponse(BaseModel):
    """Response shape — secret_ref is NEVER included."""
    id: str
    hired_instance_id: str
    skill_id: str
    customer_platform_credential_id: Optional[str] = None
    platform_key: str
    status: str
    connected_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class StartYouTubeConnectRequest(BaseModel):
    customer_id: str
    redirect_uri: str


class StartYouTubeConnectResponse(BaseModel):
    state: str
    authorization_url: str
    expires_at: datetime


class FinalizeYouTubeConnectRequest(BaseModel):
    customer_id: str
    state: str
    code: str
    redirect_uri: str


class CustomerPlatformCredentialResponse(BaseModel):
    id: str
    customer_id: str
    platform_key: str
    provider_account_id: Optional[str] = None
    display_name: Optional[str] = None
    granted_scopes: list[str]
    verification_status: str
    connection_status: str
    next_action_hint: Optional[str] = None
    suggested_channel_name: Optional[str] = None
    create_channel_url: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AttachCustomerCredentialRequest(BaseModel):
    customer_id: str
    hired_instance_id: str
    skill_id: str
    platform_key: str = "youtube"


class ValidateCustomerCredentialRequest(BaseModel):
    customer_id: str


class ValidateCustomerCredentialResponse(BaseModel):
    id: str
    customer_id: str
    platform_key: str
    provider_account_id: Optional[str] = None
    display_name: Optional[str] = None
    verification_status: str
    connection_status: str
    next_action_hint: Optional[str] = None
    suggested_channel_name: Optional[str] = None
    create_channel_url: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    channel_count: int
    total_video_count: int
    recent_short_count: int
    recent_long_video_count: int
    subscriber_count: int
    view_count: int


def _optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    return None


def _to_response(conn: PlatformConnectionModel) -> ConnectionResponse:
    """Map model → response, intentionally omitting secret_ref."""
    return ConnectionResponse(
        id=conn.id,
        hired_instance_id=conn.hired_instance_id,
        skill_id=conn.skill_id,
        customer_platform_credential_id=_optional_string(
            getattr(conn, "customer_platform_credential_id", None)
        ),
        platform_key=conn.platform_key,
        status=conn.status,
        connected_at=conn.connected_at,
        last_verified_at=conn.last_verified_at,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


def _to_customer_credential_response(
    credential: CustomerPlatformCredentialModel,
) -> CustomerPlatformCredentialResponse:
    return CustomerPlatformCredentialResponse(
        id=credential.id,
        customer_id=credential.customer_id,
        platform_key=credential.platform_key,
        provider_account_id=credential.provider_account_id,
        display_name=credential.display_name,
        granted_scopes=list(credential.granted_scopes or []),
        verification_status=credential.verification_status,
        connection_status=credential.connection_status,
        next_action_hint=_youtube_next_action_hint(credential.connection_status),
        suggested_channel_name=_youtube_suggested_channel_name(credential.connection_status),
        create_channel_url=_youtube_create_channel_url(credential.connection_status),
        token_expires_at=credential.token_expires_at,
        last_verified_at=credential.last_verified_at,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )


def _to_validated_customer_credential_response(
    result,
) -> ValidateCustomerCredentialResponse:
    credential = result.credential
    return ValidateCustomerCredentialResponse(
        id=credential.id,
        customer_id=credential.customer_id,
        platform_key=credential.platform_key,
        provider_account_id=credential.provider_account_id,
        display_name=credential.display_name,
        verification_status=credential.verification_status,
        connection_status=credential.connection_status,
        next_action_hint=_youtube_next_action_hint(credential.connection_status),
        suggested_channel_name=_youtube_suggested_channel_name(credential.connection_status),
        create_channel_url=_youtube_create_channel_url(credential.connection_status),
        token_expires_at=credential.token_expires_at,
        last_verified_at=credential.last_verified_at,
        channel_count=result.channel_count,
        total_video_count=result.total_video_count,
        recent_short_count=result.recent_short_count,
        recent_long_video_count=result.recent_long_video_count,
        subscriber_count=result.subscriber_count,
        view_count=result.view_count,
    )


def _youtube_next_action_hint(connection_status: str | None) -> Optional[str]:
    normalized = str(connection_status or "").strip().lower()
    if normalized == "connected_no_channel":
        return "create_channel_empower"
    if normalized == "connected":
        return "connected_ready"
    return None


def _youtube_suggested_channel_name(connection_status: str | None) -> Optional[str]:
    normalized = str(connection_status or "").strip().lower()
    if normalized == "connected_no_channel":
        return YouTubeConnectionService.suggested_channel_name
    return None


def _youtube_create_channel_url(connection_status: str | None) -> Optional[str]:
    normalized = str(connection_status or "").strip().lower()
    if normalized == "connected_no_channel":
        return "https://www.youtube.com/create_channel"
    return None


def _raise_youtube_connection_error(exc: YouTubeConnectionError) -> None:
    detail = str(exc)
    if detail == "youtube_oauth_not_configured":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube OAuth is not configured on the Plant backend.",
        ) from exc
    if detail == "credential_storage_failed":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube credential vault is unavailable.",
        ) from exc
    if detail == "customer_platform_credential_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube credential not found.",
        ) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


async def get_connected_platform_connection(
    db: AsyncSession,
    *,
    hired_instance_id: str,
    skill_id: str,
    platform_key: str,
) -> PlatformConnectionModel | None:
    """Return a connected platform connection for publish eligibility checks."""

    result = await db.execute(
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
        .where(PlatformConnectionModel.skill_id == skill_id)
        .where(PlatformConnectionModel.platform_key == platform_key)
        .where(PlatformConnectionModel.status == "connected")
    )
    return result.scalars().first()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{hired_instance_id}/platform-connections",
    response_model=List[ConnectionResponse],
)
async def list_connections(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[ConnectionResponse]:
    """List platform connections for a hired agent. Never returns secret_ref."""
    result = await db.execute(
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
        .order_by(PlatformConnectionModel.created_at.desc())
    )
    connections = result.scalars().all()
    return [_to_response(c) for c in connections]


@router.post(
    "/{hired_instance_id}/platform-connections",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    hired_instance_id: str,
    body: CreateConnectionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionResponse:
    """Create a platform connection record.

    Accepts secret_ref (GCP Secret Manager path) but never returns it.
    Returns 409 on duplicate (hired_instance_id, skill_id, platform_key).
    DO NOT log body.secret_ref — it is a credential reference.
    """
    if not body.secret_ref and not body.customer_platform_credential_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either secret_ref or customer_platform_credential_id is required",
        )

    conn = PlatformConnectionModel(
        id=str(uuid.uuid4()),
        hired_instance_id=hired_instance_id,
        skill_id=body.skill_id,
        customer_platform_credential_id=body.customer_platform_credential_id,
        platform_key=body.platform_key,
        secret_ref=body.secret_ref,  # stored, never returned
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(conn)
    try:
        await db.commit()
        await db.refresh(conn)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform connection for skill_id={body.skill_id} platform_key={body.platform_key} already exists",
        )
    logger.info(
        "Platform connection created: hired=%s platform=%s",
        hired_instance_id,
        body.platform_key,
        # DO NOT log body.secret_ref
    )
    return _to_response(conn)


@customer_router.post(
    "/youtube/connect/start",
    response_model=StartYouTubeConnectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_youtube_connect(
    body: StartYouTubeConnectRequest,
    db: AsyncSession = Depends(get_db_session),
) -> StartYouTubeConnectResponse:
    service = YouTubeConnectionService(db=db)
    try:
        result = await service.start_connect(customer_id=body.customer_id, redirect_uri=body.redirect_uri)
    except YouTubeConnectionError as exc:
        _raise_youtube_connection_error(exc)
    return StartYouTubeConnectResponse(
        state=result.state,
        authorization_url=result.authorization_url,
        expires_at=result.expires_at,
    )


@customer_router.post(
    "/youtube/connect/finalize",
    response_model=CustomerPlatformCredentialResponse,
)
async def finalize_youtube_connect(
    body: FinalizeYouTubeConnectRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CustomerPlatformCredentialResponse:
    service = YouTubeConnectionService(db=db)
    try:
        result = await service.finalize_connect(
            customer_id=body.customer_id,
            state=body.state,
            code=body.code,
            redirect_uri=body.redirect_uri,
        )
    except YouTubeConnectionError as exc:
        _raise_youtube_connection_error(exc)
    return _to_customer_credential_response(result.credential)


@customer_router.get(
    "/{customer_id}",
    response_model=List[CustomerPlatformCredentialResponse],
)
async def list_customer_platform_credentials(
    customer_id: str,
    platform_key: str = "youtube",
    db: AsyncSession = Depends(get_read_db_session),
) -> List[CustomerPlatformCredentialResponse]:
    service = YouTubeConnectionService(db=db)
    credentials = await service.list_credentials(customer_id=customer_id, platform_key=platform_key)
    return [_to_customer_credential_response(item) for item in credentials]


@customer_router.get(
    "/{customer_id}/{credential_id}",
    response_model=CustomerPlatformCredentialResponse,
)
async def get_customer_platform_credential(
    customer_id: str,
    credential_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> CustomerPlatformCredentialResponse:
    service = YouTubeConnectionService(db=db)
    credential = await service.get_credential(customer_id=customer_id, credential_id=credential_id)
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer platform credential not found")
    return _to_customer_credential_response(credential)


@customer_router.post(
    "/{credential_id}/attach",
    response_model=ConnectionResponse,
)
async def attach_customer_platform_credential(
    credential_id: str,
    body: AttachCustomerCredentialRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionResponse:
    service = YouTubeConnectionService(db=db)
    try:
        connection = await service.attach_connection_to_hired_agent(
            customer_id=body.customer_id,
            credential_id=credential_id,
            hired_instance_id=body.hired_instance_id,
            skill_id=body.skill_id,
            platform_key=body.platform_key,
        )
    except YouTubeConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(connection)


@customer_router.post(
    "/{credential_id}/validate",
    response_model=ValidateCustomerCredentialResponse,
)
async def validate_customer_platform_credential(
    credential_id: str,
    body: ValidateCustomerCredentialRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ValidateCustomerCredentialResponse:
    service = YouTubeConnectionService(db=db)
    try:
        result = await service.validate_connection(
            customer_id=body.customer_id,
            credential_id=credential_id,
        )
    except YouTubeConnectionError as exc:
        _raise_youtube_connection_error(exc)
    return _to_validated_customer_credential_response(result)


@router.delete(
    "/{hired_instance_id}/platform-connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_connection(
    hired_instance_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a platform connection record."""
    result = await db.execute(
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.id == connection_id)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
    )
    conn = result.scalars().first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    await db.delete(conn)
    await db.commit()
    logger.info("Platform connection deleted: id=%s hired=%s", connection_id, hired_instance_id)


@router.patch(
    "/{hired_instance_id}/platform-connections/{connection_id}/verify",
    response_model=ConnectionResponse,
)
async def verify_connection(
    hired_instance_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionResponse:
    """Mark a connection as verified (status=connected, last_verified_at=now)."""
    result = await db.execute(
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.id == connection_id)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
    )
    conn = result.scalars().first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    now = datetime.now(timezone.utc)
    conn.status = "connected"
    conn.connected_at = conn.connected_at or now
    conn.last_verified_at = now
    conn.updated_at = now
    await db.commit()
    await db.refresh(conn)
    logger.info("Platform connection verified: id=%s hired=%s", connection_id, hired_instance_id)
    return _to_response(conn)
