"""Brand voice CRUD service.

PLANT-DMA-2 E4-S1
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.brand_voice import BrandVoiceModel


async def get_brand_voice(
    customer_id: str,
    db: AsyncSession,
) -> Optional[BrandVoiceModel]:
    """Get brand voice for a customer. Returns None if not set."""
    stmt = select(BrandVoiceModel).where(BrandVoiceModel.customer_id == customer_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_brand_voice(
    customer_id: str,
    data: dict,
    db: AsyncSession,
) -> BrandVoiceModel:
    """Create or update brand voice for a customer."""
    existing = await get_brand_voice(customer_id, db)
    if existing:
        for key, value in data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        await db.flush()
        return existing

    voice = BrandVoiceModel(customer_id=customer_id, **data)
    db.add(voice)
    await db.flush()
    return voice
