from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.agent_catalog_repository import AgentCatalogRepository


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_agent_catalog_repository_lifecycle(async_session: AsyncSession):
    repo = AgentCatalogRepository(async_session)

    release = await repo.upsert_release(
        agent_id="AGT-MKT-DMA-001",
        agent_type_id="marketing.digital_marketing.v1",
        internal_definition_version_id="1.0.0",
        external_catalog_version="v1",
        public_name="Digital Marketing Agent",
        short_description="Hire-ready DMA release",
        industry_name="Marketing",
        job_role_label="Digital Marketing Strategist",
        monthly_price_inr=12000,
        trial_days=7,
        allowed_durations=["monthly", "quarterly"],
        supported_channels=["youtube"],
        approval_mode="manual_review",
    )
    await async_session.commit()

    assert release.lifecycle_state == "draft"
    assert release.approved_for_new_hire is False

    approved = await repo.approve_release(release.release_id)
    await async_session.commit()

    assert approved.lifecycle_state == "live_on_cp"
    assert approved.approved_for_new_hire is True
    assert len(await repo.list_live_releases()) == 1

    retired = await repo.retire_release(release.release_id)
    await async_session.commit()

    assert retired.lifecycle_state == "retired_from_catalog"
    assert retired.approved_for_new_hire is False
    assert retired.retired_from_catalog_at is not None
    assert await repo.list_live_releases() == []
