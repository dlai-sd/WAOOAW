from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_read_db_session
from core.routing import waooaw_router
from models.marketing_draft import MarketingDraftBatchModel, MarketingDraftPostModel
from models.publish_receipt import PublishReceiptModel

router = waooaw_router(prefix="/api/v1/publish-receipts", tags=["publish-receipts"])


class PublishReceiptResponse(BaseModel):
    id: str
    post_id: str
    destination_type: str
    success: bool
    platform_post_id: str | None = None
    published_at: datetime | None = None
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/{hired_instance_id}", response_model=List[PublishReceiptResponse])
async def list_publish_receipts(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    """List publish receipts for a hired agent instance."""
    stmt = (
        select(PublishReceiptModel)
        .join(MarketingDraftPostModel, MarketingDraftPostModel.post_id == PublishReceiptModel.post_id)
        .join(MarketingDraftBatchModel, MarketingDraftBatchModel.batch_id == MarketingDraftPostModel.batch_id)
        .where(MarketingDraftBatchModel.hired_instance_id == hired_instance_id)
        .order_by(PublishReceiptModel.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
