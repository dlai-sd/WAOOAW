"""Repository for Plant-owned agent catalog lifecycle records."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_catalog import AgentCatalogReleaseModel


class AgentCatalogRepository:
    """Persistence layer for hire-ready catalog releases."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_release_id(self, release_id: str) -> AgentCatalogReleaseModel | None:
        stmt = select(AgentCatalogReleaseModel).where(AgentCatalogReleaseModel.release_id == release_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_for_agent_id(self, agent_id: str) -> AgentCatalogReleaseModel | None:
        stmt = (
            select(AgentCatalogReleaseModel)
            .where(AgentCatalogReleaseModel.agent_id == agent_id)
            .order_by(desc(AgentCatalogReleaseModel.created_at), desc(AgentCatalogReleaseModel.external_catalog_version))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_live_release_for_agent_id(self, agent_id: str) -> AgentCatalogReleaseModel | None:
        stmt = (
            select(AgentCatalogReleaseModel)
            .where(AgentCatalogReleaseModel.agent_id == agent_id)
            .where(AgentCatalogReleaseModel.approved_for_new_hire == True)  # noqa: E712
            .where(AgentCatalogReleaseModel.retired_from_catalog_at.is_(None))
            .order_by(desc(AgentCatalogReleaseModel.updated_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_releases(self) -> list[AgentCatalogReleaseModel]:
        stmt = (
            select(AgentCatalogReleaseModel)
            .order_by(desc(AgentCatalogReleaseModel.updated_at), desc(AgentCatalogReleaseModel.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_live_releases(self) -> list[AgentCatalogReleaseModel]:
        stmt = (
            select(AgentCatalogReleaseModel)
            .where(AgentCatalogReleaseModel.approved_for_new_hire == True)  # noqa: E712
            .where(AgentCatalogReleaseModel.retired_from_catalog_at.is_(None))
            .order_by(AgentCatalogReleaseModel.public_name.asc(), desc(AgentCatalogReleaseModel.updated_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_release(
        self,
        *,
        agent_id: str,
        agent_type_id: str,
        internal_definition_version_id: str | None,
        external_catalog_version: str,
        public_name: str,
        short_description: str,
        industry_name: str,
        job_role_label: str,
        monthly_price_inr: int,
        trial_days: int,
        allowed_durations: list[str],
        supported_channels: list[str],
        approval_mode: str,
    ) -> AgentCatalogReleaseModel:
        now = datetime.now(timezone.utc)

        stmt = select(AgentCatalogReleaseModel).where(
            AgentCatalogReleaseModel.agent_id == agent_id,
            AgentCatalogReleaseModel.external_catalog_version == external_catalog_version,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.agent_type_id = agent_type_id
            existing.internal_definition_version_id = internal_definition_version_id
            existing.public_name = public_name
            existing.short_description = short_description
            existing.industry_name = industry_name
            existing.job_role_label = job_role_label
            existing.monthly_price_inr = monthly_price_inr
            existing.trial_days = trial_days
            existing.allowed_durations = list(allowed_durations)
            existing.supported_channels = list(supported_channels)
            existing.approval_mode = approval_mode
            if existing.retired_from_catalog_at is not None:
                existing.lifecycle_state = "draft"
                existing.retired_from_catalog_at = None
            existing.updated_at = now
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        created = AgentCatalogReleaseModel(
            release_id=f"CAR-{uuid4()}",
            agent_id=agent_id,
            agent_type_id=agent_type_id,
            internal_definition_version_id=internal_definition_version_id,
            external_catalog_version=external_catalog_version,
            public_name=public_name,
            short_description=short_description,
            industry_name=industry_name,
            job_role_label=job_role_label,
            monthly_price_inr=monthly_price_inr,
            trial_days=trial_days,
            allowed_durations=allowed_durations,
            supported_channels=supported_channels,
            approval_mode=approval_mode,
            lifecycle_state="draft",
            approved_for_new_hire=False,
            retired_from_catalog_at=None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(created)
        await self.session.flush()
        await self.session.refresh(created)
        return created

    async def approve_release(self, release_id: str) -> AgentCatalogReleaseModel:
        release = await self.get_by_release_id(release_id)
        if release is None:
            raise ValueError(f"Catalog release {release_id} not found")

        release.lifecycle_state = "live_on_cp"
        release.approved_for_new_hire = True
        release.retired_from_catalog_at = None
        release.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(release)
        return release

    async def retire_release(self, release_id: str) -> AgentCatalogReleaseModel:
        release = await self.get_by_release_id(release_id)
        if release is None:
            raise ValueError(f"Catalog release {release_id} not found")

        release.lifecycle_state = "retired_from_catalog"
        release.approved_for_new_hire = False
        release.retired_from_catalog_at = datetime.now(timezone.utc)
        release.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(release)
        return release
