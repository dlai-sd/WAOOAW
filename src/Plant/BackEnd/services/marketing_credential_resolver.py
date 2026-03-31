from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.platform_connection import PlatformConnectionModel


async def resolve_youtube_secret_ref(
    db: AsyncSession,
    *,
    hired_instance_id: Optional[str],
    supplied_ref: Optional[str],
) -> Optional[str]:
    """Resolve a YouTube credential identifier to the attached secret_ref.

    The frontend may hold either the attached connection's
    `customer_platform_credential_id` or the real `secret_ref`. For publish paths,
    Plant must always use the secret reference stored on the hired-agent platform
    connection record.
    """

    raw_ref = str(supplied_ref or "").strip() or None
    if not hired_instance_id or not hasattr(db, "execute"):
        return raw_ref

    stmt = (
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
        .where(PlatformConnectionModel.platform_key == "youtube")
        .order_by(PlatformConnectionModel.updated_at.desc())
    )

    if raw_ref:
        stmt = stmt.where(
            or_(
                PlatformConnectionModel.secret_ref == raw_ref,
                PlatformConnectionModel.customer_platform_credential_id == raw_ref,
            )
        )
    else:
        stmt = stmt.where(PlatformConnectionModel.status == "connected")

    result = await db.execute(stmt)
    connection = result.scalars().first()
    if connection is None:
        return raw_ref

    secret_ref = str(getattr(connection, "secret_ref", "") or "").strip()
    return secret_ref or raw_ref