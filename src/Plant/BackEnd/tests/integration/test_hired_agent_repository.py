"""Integration tests for HiredAgentRepository (PH1-3.1).

These tests require a Postgres test database and are marked as integration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.hired_agent_repository import GoalInstanceRepository, HiredAgentRepository


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_hired_agent_repository_draft_upsert_is_idempotent(async_session: AsyncSession):
    repo = HiredAgentRepository(async_session)

    created = await repo.draft_upsert(
        subscription_id="SUB-HAI-1",
        agent_id="agent-1",
        agent_type_id="marketing.digital_marketing.v1",
        customer_id="cust-1",
        nickname="N1",
        theme="dark",
        config={"foo": "bar"},
        configured=True,
    )
    await async_session.commit()

    assert created.subscription_id == "SUB-HAI-1"
    assert created.hired_instance_id
    assert created.agent_type_id == "marketing.digital_marketing.v1"
    assert created.configured is True

    updated = await repo.draft_upsert(
        subscription_id="SUB-HAI-1",
        agent_id="agent-1",
        agent_type_id="marketing.digital_marketing.v1",
        customer_id="cust-1",
        nickname="N2",
        theme="dark",
        config={"foo": "baz"},
        configured=True,
    )
    await async_session.commit()

    assert updated.hired_instance_id == created.hired_instance_id
    assert updated.nickname == "N2"
    assert updated.config["foo"] == "baz"


@pytest.mark.asyncio
async def test_hired_agent_repository_get_by_subscription_id(async_session: AsyncSession):
    repo = HiredAgentRepository(async_session)

    created = await repo.draft_upsert(
        subscription_id="SUB-HAI-2",
        agent_id="agent-2",
        agent_type_id="trading.share_trader.v1",
        customer_id="cust-2",
        nickname=None,
        theme=None,
        config={},
        configured=False,
    )
    await async_session.commit()

    fetched = await repo.get_by_subscription_id("SUB-HAI-2")
    assert fetched is not None
    assert fetched.hired_instance_id == created.hired_instance_id
    assert fetched.agent_type_id == "trading.share_trader.v1"


@pytest.mark.asyncio
async def test_hired_agent_repository_finalize_updates_trial_fields(async_session: AsyncSession):
    repo = HiredAgentRepository(async_session)

    created = await repo.draft_upsert(
        subscription_id="SUB-HAI-3",
        agent_id="agent-3",
        agent_type_id="marketing.digital_marketing.v1",
        customer_id="cust-3",
        nickname="N",
        theme="dark",
        config={"k": "v"},
        configured=True,
    )
    await async_session.commit()

    now = datetime.now(timezone.utc)
    finalized = await repo.finalize(
        hired_instance_id=created.hired_instance_id,
        agent_type_id="marketing.digital_marketing.v1",
        goals_completed=True,
        configured=True,
        trial_status="active",
        trial_start=now,
        trial_end=now + timedelta(days=7),
    )
    await async_session.commit()

    assert finalized.goals_completed is True
    assert finalized.trial_status == "active"
    assert finalized.trial_start_at == now
    assert finalized.trial_end_at == now + timedelta(days=7)


@pytest.mark.asyncio
async def test_goal_instance_repository_upsert_list_delete(async_session: AsyncSession):
    repo = GoalInstanceRepository(async_session)

    created = await repo.upsert_goal(
        hired_instance_id="HAI-1",
        goal_template_id="marketing.weekly_multichannel_batch.v1",
        frequency="weekly",
        settings={"platform": "instagram"},
    )
    await async_session.commit()

    assert created.goal_instance_id.startswith("GOI-")
    assert created.hired_instance_id == "HAI-1"
    assert created.settings["platform"] == "instagram"

    fetched = await repo.get_by_id(created.goal_instance_id)
    assert fetched is not None
    assert fetched.goal_instance_id == created.goal_instance_id

    updated = await repo.upsert_goal(
        hired_instance_id="HAI-1",
        goal_template_id="marketing.weekly_multichannel_batch.v1",
        frequency="monthly",
        settings={"platform": "linkedin"},
        goal_instance_id=created.goal_instance_id,
    )
    await async_session.commit()
    assert updated.goal_instance_id == created.goal_instance_id
    assert updated.frequency == "monthly"
    assert updated.settings["platform"] == "linkedin"

    goals = await repo.list_by_hired_instance("HAI-1")
    assert len(goals) == 1
    assert goals[0].goal_instance_id == created.goal_instance_id

    deleted = await repo.delete_goal(created.goal_instance_id)
    await async_session.commit()
    assert deleted is True

    deleted_again = await repo.delete_goal(created.goal_instance_id)
    await async_session.commit()
    assert deleted_again is False
