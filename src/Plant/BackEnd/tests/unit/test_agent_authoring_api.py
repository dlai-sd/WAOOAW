"""Unit tests for Plant agent authoring draft routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from api.v1.agent_authoring import (
    AgentAuthoringDraftResponse,
    ReviewerComment,
    get_read_repository,
    get_write_repository,
    router,
)


def _draft_response(**overrides) -> AgentAuthoringDraftResponse:
    now = datetime.now(timezone.utc)
    payload = {
        "draft_id": "AAD-1",
        "candidate_agent_type_id": "marketing.digital_marketing_agent",
        "candidate_agent_label": "Digital Marketing Agent",
        "contract_payload": {"identity": {"name": "DMA"}},
        "section_states": {"identity": "ready", "deliverables": "missing"},
        "constraint_policy": {"approval_required": True},
        "reviewer_comments": [],
        "status": "draft",
        "reviewer_id": None,
        "reviewer_name": None,
        "submitted_at": None,
        "reviewed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return AgentAuthoringDraftResponse(**payload)


@pytest.fixture
async def client() -> AsyncGenerator[tuple[httpx.AsyncClient, AsyncMock, AsyncMock], None]:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    read_repository = AsyncMock()
    write_repository = AsyncMock()

    app.dependency_overrides[get_read_repository] = lambda: read_repository
    app.dependency_overrides[get_write_repository] = lambda: write_repository

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, read_repository, write_repository


@pytest.mark.asyncio
async def test_list_drafts_returns_serialized_rows(client):
    http_client, read_repository, _ = client
    read_repository.list_drafts.return_value = [_draft_response()]

    response = await http_client.get("/api/v1/agent-authoring/drafts")

    assert response.status_code == 200
    assert response.json()[0]["draft_id"] == "AAD-1"
    read_repository.list_drafts.assert_awaited_once_with(status=None)


@pytest.mark.asyncio
async def test_get_draft_returns_not_found(client):
    http_client, read_repository, _ = client
    read_repository.get_by_id.return_value = None

    response = await http_client.get("/api/v1/agent-authoring/drafts/AAD-missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Draft not found"


@pytest.mark.asyncio
async def test_save_draft_commits_and_returns_response(client):
    http_client, _, write_repository = client
    draft = _draft_response()
    write_repository.save_draft.return_value = draft
    write_repository.session.commit = AsyncMock()

    response = await http_client.post(
        "/api/v1/agent-authoring/drafts",
        json={
            "candidate_agent_type_id": "marketing.digital_marketing_agent",
            "candidate_agent_label": "Digital Marketing Agent",
            "contract_payload": {"identity": {"name": "DMA"}},
            "section_states": {"identity": "ready", "deliverables": "missing"},
            "constraint_policy": {"approval_required": True},
        },
    )

    assert response.status_code == 200
    assert response.json()["section_states"]["deliverables"] == "missing"
    write_repository.save_draft.assert_awaited_once()
    write_repository.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_changes_returns_comments(client):
    http_client, _, write_repository = client
    draft = _draft_response(
        status="changes_requested",
        reviewer_comments=[
            ReviewerComment(
                section_key="identity",
                comment="Clarify ICP.",
                severity="changes_requested",
            )
        ],
    )
    write_repository.request_changes.return_value = draft
    write_repository.session.commit = AsyncMock()

    response = await http_client.post(
        "/api/v1/agent-authoring/drafts/AAD-1/changes-requested",
        json={
            "reviewer_id": "reviewer-1",
            "reviewer_name": "PP Reviewer",
            "reviewer_comments": [
                {
                    "section_key": "identity",
                    "comment": "Clarify ICP.",
                    "severity": "changes_requested",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "changes_requested"
    assert response.json()["reviewer_comments"][0]["section_key"] == "identity"
