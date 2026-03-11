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
from models.platform_connection import PlatformConnectionModel

router = waooaw_router(prefix="/hired-agents", tags=["platform-connections"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CreateConnectionRequest(BaseModel):
    skill_id: str
    platform_key: str
    # GCP Secret Manager resource path ONLY — never the raw secret value
    # e.g. "projects/waooaw-oauth/secrets/hired-abc123-delta-exchange/versions/latest"
    secret_ref: str


class ConnectionResponse(BaseModel):
    """Response shape — secret_ref is NEVER included."""
    id: str
    hired_instance_id: str
    skill_id: str
    platform_key: str
    status: str
    connected_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


def _to_response(conn: PlatformConnectionModel) -> ConnectionResponse:
    """Map model → response, intentionally omitting secret_ref."""
    return ConnectionResponse(
        id=conn.id,
        hired_instance_id=conn.hired_instance_id,
        skill_id=conn.skill_id,
        platform_key=conn.platform_key,
        status=conn.status,
        connected_at=conn.connected_at,
        last_verified_at=conn.last_verified_at,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


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
    conn = PlatformConnectionModel(
        id=str(uuid.uuid4()),
        hired_instance_id=hired_instance_id,
        skill_id=body.skill_id,
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
