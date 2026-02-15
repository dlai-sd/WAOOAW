"""Repository for Subscription database operations.

Provides async CRUD operations for subscriptions table.

Phase 1 scope:
- Upsert by subscription_id (idempotent writes)
- Fetch by subscription_id
- List by customer_id
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscription import SubscriptionModel


class SubscriptionRepository:
    """Repository for subscription persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, subscription_id: str) -> SubscriptionModel | None:
        stmt = select(SubscriptionModel).where(SubscriptionModel.subscription_id == subscription_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_customer_id(self, customer_id: str) -> list[SubscriptionModel]:
        stmt = (
            select(SubscriptionModel)
            .where(SubscriptionModel.customer_id == customer_id)
            .order_by(SubscriptionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        subscription_id: str,
        agent_id: str,
        duration: str,
        customer_id: str | None,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool,
        ended_at: datetime | None,
        now: datetime,
    ) -> SubscriptionModel:
        existing = await self.get_by_id(subscription_id)
        if existing:
            existing.agent_id = agent_id
            existing.duration = duration
            existing.customer_id = customer_id
            existing.status = status
            existing.current_period_start = current_period_start
            existing.current_period_end = current_period_end
            existing.cancel_at_period_end = cancel_at_period_end
            existing.ended_at = ended_at
            existing.updated_at = now
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        new_record = SubscriptionModel(
            subscription_id=subscription_id,
            agent_id=agent_id,
            duration=duration,
            customer_id=customer_id,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            ended_at=ended_at,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_record)
        await self.session.flush()
        await self.session.refresh(new_record)
        return new_record
