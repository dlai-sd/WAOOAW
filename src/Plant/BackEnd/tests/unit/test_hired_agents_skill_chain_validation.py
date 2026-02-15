"""Unit tests for SK-3.1 hire-time skill-chain enforcement."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from models.agent import Agent
from models.job_role import JobRole
from models.skill import Skill


def _result_first(obj):
    scalars = Mock()
    scalars.first.return_value = obj
    result = Mock()
    result.scalars.return_value = scalars
    return result


def _result_all(items):
    scalars = Mock()
    scalars.all.return_value = items
    result = Mock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.unit
def test_finalize_fails_when_any_required_skill_not_certified(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")
    monkeypatch.setenv("HIRE_ENFORCE_SKILL_CHAIN", "true")

    from fastapi.testclient import TestClient

    from api.v1 import hired_agents_simple
    from main import app

    # Keep global in-memory stores deterministic.
    hired_agents_simple._by_id.clear()
    hired_agents_simple._by_subscription.clear()

    skill_certified = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Certified Skill",
        description="desc",
        category="technical",
        status="certified",
    )
    skill_pending = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Pending Skill",
        description="desc",
        category="technical",
        status="pending_certification",
    )
    job_role = JobRole(
        id=uuid.uuid4(),
        entity_type="JobRole",
        name="Role",
        description="role",
        required_skills=[skill_certified.id, skill_pending.id],
        seniority_level="mid",
        status="active",
    )
    agent = Agent(
        id=uuid.uuid4(),
        entity_type="Agent",
        name="Agent",
        skill_id=skill_certified.id,
        job_role_id=job_role.id,
        industry_id=uuid.uuid4(),
        status="active",
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _result_first(agent),
            _result_first(job_role),
            _result_all([skill_certified, skill_pending]),
        ]
    )

    async def override_db():
        yield db

    app.dependency_overrides[hired_agents_simple._get_hired_agents_db_session] = override_db

    try:
        with TestClient(app) as client:
            checkout = client.post(
                "/api/v1/payments/coupon/checkout",
                json={
                    "coupon_code": "WAOOAW100",
                    "agent_id": str(agent.id),
                    "duration": "monthly",
                    "customer_id": "cust-1",
                },
            )
            assert checkout.status_code == 200
            subscription_id = checkout.json()["subscription_id"]

            hired_instance_id = "HAI-test"
            now = datetime.now(timezone.utc)
            record = hired_agents_simple._HiredAgentRecord(
                hired_instance_id=hired_instance_id,
                subscription_id=subscription_id,
                agent_id=str(agent.id),
                customer_id="cust-1",
                nickname="N",
                theme="dark",
                config={},
                configured=True,
                goals_completed=False,
                active=True,
                trial_status="not_started",
                trial_start_at=None,
                trial_end_at=None,
                created_at=now,
                updated_at=now,
            )
            hired_agents_simple._by_id[hired_instance_id] = record
            hired_agents_simple._by_subscription[subscription_id] = hired_instance_id

            finalize = client.post(
                f"/api/v1/hired-agents/{hired_instance_id}/finalize",
                json={"customer_id": "cust-1", "goals_completed": True},
            )

        assert finalize.status_code == 422
        detail = finalize.json().get("detail")
        assert isinstance(detail, dict)
        assert str(skill_pending.id) in (detail.get("uncertified_skill_ids") or [])
    finally:
        app.dependency_overrides.pop(hired_agents_simple._get_hired_agents_db_session, None)
        hired_agents_simple._by_id.clear()
        hired_agents_simple._by_subscription.clear()


@pytest.mark.unit
def test_draft_upsert_fails_closed_when_required_skills_missing_or_uncertified(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")
    monkeypatch.setenv("HIRE_ENFORCE_SKILL_CHAIN", "true")

    from fastapi.testclient import TestClient

    from api.v1 import hired_agents_simple
    from main import app

    # Keep global in-memory stores deterministic.
    hired_agents_simple._by_id.clear()
    hired_agents_simple._by_subscription.clear()

    missing_skill_id = uuid.uuid4()
    skill_uncertified = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Uncertified Skill",
        description="desc",
        category="technical",
        status="pending_certification",
    )
    job_role = JobRole(
        id=uuid.uuid4(),
        entity_type="JobRole",
        name="Role",
        description="role",
        required_skills=[missing_skill_id, skill_uncertified.id],
        seniority_level="mid",
        status="active",
    )
    agent = Agent(
        id=uuid.uuid4(),
        entity_type="Agent",
        name="Agent",
        skill_id=skill_uncertified.id,
        job_role_id=job_role.id,
        industry_id=uuid.uuid4(),
        status="active",
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _result_first(agent),
            _result_first(job_role),
            _result_all([skill_uncertified]),
        ]
    )

    async def override_db():
        yield db

    app.dependency_overrides[hired_agents_simple._get_hired_agents_db_session] = override_db

    try:
        with TestClient(app) as client:
            checkout = client.post(
                "/api/v1/payments/coupon/checkout",
                json={
                    "coupon_code": "WAOOAW100",
                    "agent_id": str(agent.id),
                    "duration": "monthly",
                    "customer_id": "cust-1",
                },
            )
            assert checkout.status_code == 200
            subscription_id = checkout.json()["subscription_id"]

            resp = client.put(
                "/api/v1/hired-agents/draft",
                json={
                    "subscription_id": subscription_id,
                    "agent_id": str(agent.id),
                    "customer_id": "cust-1",
                    "nickname": "N",
                    "theme": "dark",
                    "config": {},
                },
            )

        assert resp.status_code == 422
        detail = resp.json().get("detail")
        assert isinstance(detail, dict)
        assert str(missing_skill_id) in (detail.get("missing_skill_ids") or [])
        assert str(skill_uncertified.id) in (detail.get("uncertified_skill_ids") or [])
    finally:
        app.dependency_overrides.pop(hired_agents_simple._get_hired_agents_db_session, None)
        hired_agents_simple._by_id.clear()
        hired_agents_simple._by_subscription.clear()


@pytest.mark.unit
def test_db_mode_does_not_enforce_skill_chain_when_flag_unset(monkeypatch):
    """Phase-1 compatibility: DB mode should not require Genesis skills by default."""

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("PAYMENTS_MODE", "coupon")
    monkeypatch.setenv("PERSISTENCE_MODE", "db")
    monkeypatch.delenv("HIRE_ENFORCE_SKILL_CHAIN", raising=False)

    from fastapi.testclient import TestClient

    from api.v1 import hired_agents_simple
    from main import app

    # Keep global in-memory stores deterministic.
    hired_agents_simple._by_id.clear()
    hired_agents_simple._by_subscription.clear()

    # Provide a DB object, but make any execute call fail so we can prove
    # SK-3.1 queries are not executed when the flag is unset.
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=AssertionError("SK-3.1 should not query DB when flag is unset"))

    async def override_db():
        yield db

    app.dependency_overrides[hired_agents_simple._get_hired_agents_db_session] = override_db

    try:
        with TestClient(app) as client:
            checkout = client.post(
                "/api/v1/payments/coupon/checkout",
                json={
                    "coupon_code": "WAOOAW100",
                    "agent_id": "AGT-MKT-HEALTH-001",
                    "duration": "monthly",
                    "customer_id": "cust-1",
                },
            )
            assert checkout.status_code == 200
            subscription_id = checkout.json()["subscription_id"]

            draft = client.put(
                "/api/v1/hired-agents/draft",
                json={
                    "subscription_id": subscription_id,
                    "agent_id": "AGT-MKT-HEALTH-001",
                    "customer_id": "cust-1",
                    "nickname": "Marketer",
                    "theme": "dark",
                    "config": {
                        "primary_language": "en",
                        "timezone": "Asia/Kolkata",
                        "brand_name": "Clinic",
                        "offerings_services": ["Dental"],
                        "location": "Mumbai",
                        "platforms": [{"platform": "instagram", "credential_ref": "CRED-1"}],
                    },
                },
            )
            assert draft.status_code == 200

            hired_instance_id = draft.json()["hired_instance_id"]
            finalize = client.post(
                f"/api/v1/hired-agents/{hired_instance_id}/finalize",
                json={"customer_id": "cust-1", "goals_completed": True},
            )
            assert finalize.status_code == 200
            assert finalize.json()["trial_status"] == "active"
    finally:
        app.dependency_overrides.pop(hired_agents_simple._get_hired_agents_db_session, None)
        hired_agents_simple._by_id.clear()
        hired_agents_simple._by_subscription.clear()
