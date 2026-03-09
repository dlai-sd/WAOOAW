"""PATCH /v1/skill-configs/{hired_instance_id}/{skill_id}

Allows customers to update the `customer_fields` portion of a skill config.
PP-locked fields are read-only and cannot be modified via this endpoint.
"""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.agent_skills import RuntimeSkillResponse, get_runtime_skill_response_for_hire
from core.routing import waooaw_router
from core.database import get_db_session
from models.skill_config import SkillConfigModel

router = waooaw_router(prefix="/skill-configs", tags=["skill-configs"])
hired_agent_router = waooaw_router(prefix="/hired-agents", tags=["skill-configs"])


class CustomerFieldsUpdate(BaseModel):
    customer_fields: dict


async def _update_customer_fields(
    *,
    hired_instance_id: str,
    skill_id: str,
    customer_fields: dict,
    db: AsyncSession,
) -> SkillConfigModel:
    result = await db.execute(
        select(SkillConfigModel).where(
            SkillConfigModel.hired_instance_id == hired_instance_id,
            SkillConfigModel.skill_id == skill_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="skill_config not found")

    row.customer_fields = customer_fields
    await db.commit()
    await db.refresh(row)
    return row


async def _runtime_response_or_fallback(
    *,
    hired_instance_id: str,
    skill_id: str,
    row: SkillConfigModel,
    db: AsyncSession,
) -> RuntimeSkillResponse | dict:
    try:
        runtime_skill = await get_runtime_skill_response_for_hire(
            hired_instance_id=hired_instance_id,
            skill_id=skill_id,
            db=db,
        )
        return runtime_skill.model_copy(
            update={
                "customer_fields": dict(row.customer_fields or {}),
                "platform_fields": dict(row.pp_locked_fields or {}),
                "goal_config": dict(row.customer_fields or {}),
            }
        )
    except HTTPException:
        return {
            "skill_id": skill_id,
            "name": skill_id,
            "display_name": skill_id,
            "category": None,
            "description": None,
            "platform_fields": dict(row.pp_locked_fields or {}),
            "customer_fields": dict(row.customer_fields or {}),
            "goal_schema": None,
            "goal_config": dict(row.customer_fields or {}),
            "status": "configured",
        }


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
    row = await _update_customer_fields(
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        customer_fields=body.customer_fields,
        db=db,
    )
    return await _runtime_response_or_fallback(
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        row=row,
        db=db,
    )


@hired_agent_router.patch("/{hired_instance_id}/skills/{skill_id}/customer-config")
async def update_customer_config(
    hired_instance_id: str,
    skill_id: str,
    body: CustomerFieldsUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    row = await _update_customer_fields(
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        customer_fields=body.customer_fields,
        db=db,
    )
    return await _runtime_response_or_fallback(
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        row=row,
        db=db,
    )
