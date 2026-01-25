"""src/Plant/BackEnd/tests/conftest.py

Test fixtures and configuration for Plant backend tests.

These tests are executed in Docker in CI (via the per-service Test Agent).
They should not depend on a developer's local Postgres.
"""

import os
from pathlib import Path
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import event
from testcontainers.postgres import PostgresContainer
import uuid
from datetime import datetime

from core.database import Base, get_connector, DatabaseConnector
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team
from models.agent import Agent
from models.industry import Industry


# ========== SESSION & EVENT LOOP ==========
# Use pytest-asyncio's default event loop management
# Don't override event_loop fixture to avoid deprecation warnings


# ========== DATABASE CONFIGURATION ==========
@pytest.fixture(scope="session")
def test_db_url():
    """
    Database URL for integration tests.

    Defaults to the docker-compose test database (host port 5433) so local runs
    work after `docker compose -f tests/docker-compose.test.yml up -d`.
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://waooaw_test:waooaw_test_password@localhost:5433/waooaw_test_db",
    )


def _apply_alembic_migrations(db_url: str) -> None:
    """Apply Alembic migrations to a fresh test database.

    We stop at revision 006 to include the Trial API tables.
    Later migrations (e.g. 007) may require extra extensions/services.
    """

    # Reset the schema to keep runs deterministic (important when the same
    # docker-compose database is reused across multiple suite invocations).
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine.url import make_url

    parsed = make_url(db_url)
    if parsed.database and "test" not in parsed.database.lower():
        raise RuntimeError(
            f"Refusing to reset non-test database: {parsed.database!r}. "
            "Set DATABASE_URL to a dedicated *_test* database."
        )

    sync_url = parsed.set(drivername="postgresql+psycopg2")
    sync_engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    with sync_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    sync_engine.dispose()

    from alembic import command
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[1]
    alembic_ini = backend_root / "alembic.ini"
    cfg = Config(alembic_ini.as_posix())
    cfg.set_main_option("script_location", (backend_root / "database" / "migrations").as_posix())
    cfg.set_main_option("prepend_sys_path", backend_root.as_posix())

    # Ensure Settings sees the test DB url (env.py reads from settings.database_url).
    os.environ["DATABASE_URL"] = db_url

    command.upgrade(cfg, "006_trial_tables")


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_database_once(test_db_url: str) -> None:
    """Apply migrations once per pytest session.

    The per-test `async_engine` fixture is function-scoped (bound to the current
    event loop) to avoid asyncpg/pytest-asyncio loop-mismatch errors.
    """

    _apply_alembic_migrations(test_db_url)


@pytest.fixture
async def async_engine(test_db_url: str):
    """
    Create async SQLAlchemy engine for tests.
    Function-scoped to ensure the engine is created within the active event loop.
    """
    engine = create_async_engine(
        test_db_url,
        echo=False,
        connect_args={"timeout": 10},  # Changed from connect_timeout to timeout for asyncpg
    )
    
    yield engine
    
    # Cleanup - just dispose connections, don't drop tables
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for each test.
    Uses nested transaction (SAVEPOINT) for complete isolation.
    Auto-rolls back after test completes.
    """
    async with async_engine.connect() as connection:
        # Start an explicit outer transaction on the connection.
        outer = await connection.begin()

        async_session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        async with async_session_maker() as session:
            # Start the first nested transaction (SAVEPOINT).
            await connection.begin_nested()

            # When the nested transaction ends (e.g., via session.commit()),
            # automatically start a new SAVEPOINT so the session stays usable.
            @event.listens_for(session.sync_session, "after_transaction_end")
            def _restart_savepoint(sess, transaction):  # type: ignore[no-redef]
                if transaction.nested and not transaction._parent.nested:
                    connection.sync_connection.begin_nested()

            yield session

        # Roll back everything done during the test.
        await outer.rollback()


# ========== SEED DATA FACTORIES ==========
@pytest.fixture
async def create_test_skill(async_session: AsyncSession):
    """Factory for creating test Skill entities."""
    async def _create_skill(
        name: str = "Python",
        description: str = "Test skill description",
        category: str = "technical",
        embedding: list = None
    ) -> Skill:
        if embedding is None:
            embedding = [0.1] * 384  # MiniLM-384 dimension
        
        skill = Skill(
            id=uuid.uuid4(),
            entity_type="Skill",
            name=name,
            description=description,
            category=category,
            embedding_384=embedding,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(skill)
        await async_session.commit()
        return skill
    
    return _create_skill


@pytest.fixture
async def create_test_industry(async_session: AsyncSession):
    """Factory for creating test Industry entities."""
    async def _create_industry(
        name: str = "Marketing",
        description: str = "Marketing industry"
    ) -> Industry:
        industry = Industry(
            id=uuid.uuid4(),
            entity_type="Industry",
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(industry)
        await async_session.commit()
        return industry
    
    return _create_industry


@pytest.fixture
async def create_test_job_role(async_session: AsyncSession, create_test_skill):
    """Factory for creating test JobRole entities."""
    async def _create_job_role(
        name: str = "Senior Developer",
        required_skills: list = None,
        description: str = "Test job role",
        seniority_level: str = "mid",
        industry_id: uuid.UUID | None = None,
    ) -> JobRole:
        if required_skills is None:
            skill = await create_test_skill(name=f"{name} Skill")
            required_skills = [skill.id]
        
        job_role = JobRole(
            id=uuid.uuid4(),
            entity_type="JobRole",
            name=name,
            description=description,
            required_skills=required_skills,
            seniority_level=seniority_level,
            industry_id=industry_id,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(job_role)
        await async_session.commit()
        return job_role
    
    return _create_job_role


@pytest.fixture
async def create_test_agent(async_session: AsyncSession, create_test_skill, create_test_industry, create_test_job_role):
    """Factory for creating test Agent entities."""
    async def _create_agent(
        name: str = "TestAgent",
        industry_id: uuid.UUID | None = None
    ) -> Agent:
        skill = await create_test_skill(name=f"{name} Skill")

        if industry_id is None:
            industry = await create_test_industry(name=f"{name} Industry")
            industry_id = industry.id

        job_role = await create_test_job_role(name=f"{name} JobRole")
        
        agent = Agent(
            id=uuid.uuid4(),
            entity_type="Agent",
            name=name,
            skill_id=skill.id,
            job_role_id=job_role.id,
            industry_id=industry_id,
            created_at=datetime.utcnow(),
            status="active",
        )
        async_session.add(agent)
        await async_session.commit()
        return agent
    
    return _create_agent


@pytest.fixture
async def test_db_cleanup(async_session: AsyncSession):
    """
    Cleanup fixture - called after each test to ensure isolation.
    """
    yield
    # Rollback any uncommitted transactions
    await async_session.rollback()
def genesis_skill_data():
    """
    Sample skill data for testing.
    """
    return {
        "name": "Test Skill",
        "description": "A test skill for unit testing",
        "category": "technical",
        "governance_agent_id": "genesis",
    }


@pytest.fixture
def genesis_job_role_data():
    """
    Sample job role data for testing.
    """
    return {
        "name": "Test Job Role",
        "description": "A test job role",
        "required_skills": [],
        "seniority_level": "mid",
        "governance_agent_id": "genesis",
    }


@pytest.fixture
def rsa_keypair():
    """
    Generate RSA keypair for cryptography tests.
    """
    from security.cryptography import generate_rsa_keypair
    return generate_rsa_keypair()
