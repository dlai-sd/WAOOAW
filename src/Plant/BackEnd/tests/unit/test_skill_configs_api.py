"""Unit tests for skill_configs API endpoint (EXEC-ENGINE-001 E1-S3).

Tests the PATCH /api/v1/skill-configs/{hired_instance_id}/{skill_id} endpoint
using TestClient with a mocked DB session.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_skill_configs_api.py -v --cov=api --cov-fail-under=80
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.skill_config import SkillConfigModel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_skill_config_row(
    id: str = "sc-001",
    hired_instance_id: str = "hired-001",
    skill_id: str = "skill-001",
    customer_fields: dict | None = None,
) -> SkillConfigModel:
    now = datetime.now(timezone.utc)
    row = SkillConfigModel(
        id=id,
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        definition_version_id="v1",
        pp_locked_fields={"max_risk_pct": 0.02},
        customer_fields=customer_fields or {},
        created_at=now,
        updated_at=now,
    )
    return row


def _make_mock_db(row: SkillConfigModel | None) -> AsyncMock:
    """Return async DB session mock that returns `row` from execute."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = row

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ── E1-S3-T2: PATCH returns 200 with updated customer_fields ─────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_patch_skill_config_success():
    """E1-S3-T2: PATCH with valid ids returns 200 and updated customer_fields."""
    from api.v1.skill_configs import update_skill_config, CustomerFieldsUpdate

    row = _make_skill_config_row()
    db = _make_mock_db(row)
    body = CustomerFieldsUpdate(customer_fields={"rsi_period": 14})

    response = await update_skill_config(
        hired_instance_id="hired-001",
        skill_id="skill-001",
        body=body,
        db=db,
    )

    assert response["id"] == "sc-001"
    assert response["customer_fields"] == {"rsi_period": 14}
    db.commit.assert_awaited_once()


# ── E1-S3-T3: PATCH with unknown hired_instance_id returns 404 ───────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_patch_skill_config_not_found():
    """E1-S3-T3: PATCH with unknown hired_instance_id raises HTTP 404."""
    from fastapi import HTTPException

    from api.v1.skill_configs import update_skill_config, CustomerFieldsUpdate

    db = _make_mock_db(None)  # No row found
    body = CustomerFieldsUpdate(customer_fields={"rsi_period": 14})

    with pytest.raises(HTTPException) as exc_info:
        await update_skill_config(
            hired_instance_id="unknown-hired",
            skill_id="skill-001",
            body=body,
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert "skill_config not found" in exc_info.value.detail
