"""PATCH /v1/skill-configs/{hired_instance_id}/{skill_id}

Allows customers to update the `customer_fields` portion of a skill config.
PP-locked fields are read-only and cannot be modified via this endpoint.
"""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.routing import waooaw_router
from core.database import get_db_session
from models.skill_config import SkillConfigModel

router = waooaw_router(prefix="/skill-configs", tags=["skill-configs"])


class CustomerFieldsUpdate(BaseModel):
    customer_fields: dict


@router.patch("/{hired_instance_id}/{skill_id}")
async def update_skill_config(
    hired_instance_id: str,
    skill_id: str,
    body: CustomerFieldsUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update the customer-editable fields of a skill config.

    Only `customer_fields` may be updated. PP-locked fields are immutable.
    Returns HTTP 404 when no skill config exists for the given identifiers.
    """
    from sqlalchemy import select

    result = await db.execute(
        select(SkillConfigModel).where(
            SkillConfigModel.hired_instance_id == hired_instance_id,
            SkillConfigModel.skill_id == skill_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="skill_config not found")

    row.customer_fields = body.customer_fields
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "customer_fields": row.customer_fields}
