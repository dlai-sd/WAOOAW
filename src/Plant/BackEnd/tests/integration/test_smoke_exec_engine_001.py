"""Smoke test — verifies all new EXEC-ENGINE-001 Iteration 1 tables exist (E2-S2).

Runs after `alembic upgrade head` to confirm that flow_runs, component_runs,
and skill_configs tables are present and queryable.

Requires: live Postgres DB with migrations applied (integration test).

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/integration/test_smoke_exec_engine_001.py -v
"""
from __future__ import annotations

import pytest
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_new_tables_exist(async_session):
    """E2-S2-T1: flow_runs, component_runs, skill_configs all return COUNT(*) = 0."""
    for table in ("flow_runs", "component_runs", "skill_configs"):
        result = await async_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        assert count == 0, f"Table {table!r} not found or not empty after migration"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hired_agents_has_definition_version_id_column(async_session):
    """E2-S1: hired_agents table has definition_version_id column after migration."""
    result = await async_session.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'hired_agents'
              AND column_name = 'definition_version_id'
            """
        )
    )
    rows = result.fetchall()
    assert len(rows) == 1, "definition_version_id column not found in hired_agents"
