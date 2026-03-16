"""Integration tests for Plant agent authoring draft persistence."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.agent_authoring_draft_repository import AgentAuthoringDraftRepository


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_save_and_get_draft(async_session: AsyncSession):
    repository = AgentAuthoringDraftRepository(async_session)

    created = await repository.save_draft(
        draft_id=None,
        candidate_agent_type_id="marketing.digital_marketing_agent",
        candidate_agent_label="Digital Marketing Agent",
        contract_payload={"identity": {"name": "DMA"}},
        section_states={"identity": "ready", "deliverables": "missing"},
        constraint_policy={"approval_required": True},
    )
    await async_session.commit()

    retrieved = await repository.get_by_id(created.draft_id)

    assert retrieved is not None
    assert retrieved.candidate_agent_type_id == "marketing.digital_marketing_agent"
    assert retrieved.section_states == {
        "identity": "ready",
        "deliverables": "missing",
    }
    assert retrieved.constraint_policy == {"approval_required": True}
    assert retrieved.status == "draft"


@pytest.mark.asyncio
async def test_submit_request_changes_and_approve(async_session: AsyncSession):
    repository = AgentAuthoringDraftRepository(async_session)

    created = await repository.save_draft(
        draft_id=None,
        candidate_agent_type_id="marketing.digital_marketing_agent",
        candidate_agent_label="Digital Marketing Agent",
        contract_payload={"identity": {"name": "DMA"}},
        section_states={"identity": "ready"},
        constraint_policy={},
    )
    await async_session.commit()

    submitted = await repository.submit_for_review(created.draft_id)
    await async_session.commit()
    assert submitted is not None
    assert submitted.status == "in_review"
    assert submitted.submitted_at is not None

    changed = await repository.request_changes(
        created.draft_id,
        reviewer_comments=[
            {
                "section_key": "identity",
                "comment": "Clarify target buyer profile.",
                "severity": "changes_requested",
            }
        ],
        reviewer_id="reviewer-1",
        reviewer_name="PP Reviewer",
    )
    await async_session.commit()
    assert changed is not None
    assert changed.status == "changes_requested"
    assert changed.reviewer_comments[0]["section_key"] == "identity"

    resubmitted = await repository.submit_for_review(created.draft_id)
    await async_session.commit()
    assert resubmitted is not None
    assert resubmitted.status == "in_review"

    approved = await repository.approve(
        created.draft_id,
        reviewer_id="reviewer-2",
        reviewer_name="Approver",
    )
    await async_session.commit()
    assert approved is not None
    assert approved.status == "approved"
    assert approved.reviewed_at is not None


@pytest.mark.asyncio
async def test_patch_constraint_policy(async_session: AsyncSession):
    repository = AgentAuthoringDraftRepository(async_session)

    created = await repository.save_draft(
        draft_id=None,
        candidate_agent_type_id="marketing.digital_marketing_agent",
        candidate_agent_label="Digital Marketing Agent",
        contract_payload={},
        section_states={},
        constraint_policy={"approval_required": True},
    )
    await async_session.commit()

    updated = await repository.patch_constraint_policy(
        created.draft_id,
        constraint_policy={"approval_required": False, "risk_tier": "moderate"},
    )
    await async_session.commit()

    assert updated is not None
    assert updated.constraint_policy == {
        "approval_required": False,
        "risk_tier": "moderate",
    }