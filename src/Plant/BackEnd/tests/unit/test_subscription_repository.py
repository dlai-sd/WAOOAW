"""Integration tests for SubscriptionRepository (PH1-2.1).

These tests require a Postgres test database and are marked as integration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.subscription_repository import SubscriptionRepository


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_subscription_repository_upsert_is_idempotent(async_session: AsyncSession):
    repo = SubscriptionRepository(async_session)

    now1 = datetime.now(timezone.utc)

    created = await repo.upsert(
        subscription_id="SUB-1",
        agent_id="agent-1",
        duration="monthly",
        customer_id="cust-1",
        status="active",
        current_period_start=now1,
        current_period_end=now1 + timedelta(days=30),
        cancel_at_period_end=False,
        ended_at=None,
        now=now1,
    )
    await async_session.commit()

    assert created.subscription_id == "SUB-1"
    assert created.status == "active"
    assert created.created_at == now1

    now2 = now1 + timedelta(hours=1)

    updated = await repo.upsert(
        subscription_id="SUB-1",
        agent_id="agent-1",
        duration="quarterly",
        customer_id="cust-1",
        status="active",
        current_period_start=now1,
        current_period_end=now1 + timedelta(days=90),
        cancel_at_period_end=True,
        ended_at=None,
        now=now2,
    )
    await async_session.commit()

    assert updated.subscription_id == "SUB-1"
    assert updated.duration == "quarterly"
    assert updated.cancel_at_period_end is True
    # Upsert updates updated_at but preserves created_at.
    assert updated.created_at == now1
    assert updated.updated_at == now2


@pytest.mark.asyncio
async def test_subscription_repository_list_by_customer_id(async_session: AsyncSession):
    repo = SubscriptionRepository(async_session)

    now = datetime.now(timezone.utc)

    await repo.upsert(
        subscription_id="SUB-A",
        agent_id="agent-1",
        duration="monthly",
        customer_id="cust-1",
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        ended_at=None,
        now=now,
    )

    await repo.upsert(
        subscription_id="SUB-B",
        agent_id="agent-2",
        duration="monthly",
        customer_id="cust-1",
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        ended_at=None,
        now=now + timedelta(minutes=5),
    )

    await repo.upsert(
        subscription_id="SUB-C",
        agent_id="agent-3",
        duration="monthly",
        customer_id="cust-2",
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        ended_at=None,
        now=now,
    )

    await async_session.commit()

    subs = await repo.list_by_customer_id("cust-1")
    assert [s.subscription_id for s in subs] == ["SUB-B", "SUB-A"]
