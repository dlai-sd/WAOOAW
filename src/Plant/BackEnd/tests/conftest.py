"""src/Plant/BackEnd/tests/conftest.py

Test fixtures and configuration for Plant backend tests.

These tests are executed in Docker in CI (via the per-service Test Agent).
They should not depend on a developer's local Postgres.
"""

import os
import sys
import importlib
from copy import deepcopy
from pathlib import Path
from typing import AsyncGenerator
import logging

import pytest
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import event
import uuid
from datetime import datetime

from core.database import Base, get_connector, DatabaseConnector
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team
from models.agent import Agent
from models.industry import Industry
from services.draft_batches import DraftBatchRecord, DraftPostRecord, _UNSET


@pytest.fixture(autouse=True)
def _default_persistence_mode_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default to in-memory persistence for unit-style tests.

    CI's Plant unit-test job does not provide a Postgres instance, but runtime
    defaults may be DB-first. Keep tests DB-free unless a specific test opts in
    by setting PERSISTENCE_MODE=db.
    """

    if "PERSISTENCE_MODE" not in os.environ:
        monkeypatch.setenv("PERSISTENCE_MODE", "memory")

    if "CAMPAIGN_PERSISTENCE_MODE" not in os.environ:
        monkeypatch.setenv("CAMPAIGN_PERSISTENCE_MODE", "memory")

    campaigns_module = sys.modules.get("api.v1.campaigns")
    if campaigns_module is not None:
        monkeypatch.setattr(campaigns_module, "CAMPAIGN_PERSISTENCE_MODE", "memory", raising=False)


@pytest.fixture(autouse=True)
def _reset_python_logging_state() -> None:
    """Keep caplog-based tests deterministic.

    Some tests/dependencies can call `logging.disable(...)` or mark specific
    loggers as disabled, which prevents pytest's `caplog` from seeing records
    when the whole suite runs (even if an individual test passes in isolation).
    """

    logging.disable(logging.NOTSET)

    root_logger = logging.getLogger()
    root_logger.disabled = False

    # Ensure no library/module logger stays disabled across tests.
    for maybe_logger in logging.root.manager.loggerDict.values():
        if isinstance(maybe_logger, logging.Logger):
            maybe_logger.disabled = False

    for logger_name in (
        "integrations.social.metrics",
        "integrations.social.retry_handler",
    ):
        logging.getLogger(logger_name).disabled = False


@pytest.fixture
def test_client(monkeypatch):
    """Synchronous FastAPI test client for performance-style tests."""
    if "PERSISTENCE_MODE" not in os.environ:
        monkeypatch.setenv("PERSISTENCE_MODE", "memory")

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_test_client(monkeypatch, test_db_url, migrated_db):
    _apply_alembic_migrations(test_db_url)
    monkeypatch.setenv("DATABASE_URL", test_db_url)

    import core.config as config_module
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    import core.database as database_module
    database_module.settings = config_module.settings
    database_module._connector = database_module.DatabaseConnector()

    import main as main_module
    importlib.reload(main_module)

    from fastapi.testclient import TestClient

    with TestClient(main_module.app) as client:
        yield client


class _DummyAsyncSession:
    async def commit(self) -> None:
        return None

    async def close(self) -> None:
        return None


class _InMemoryDraftBatchStore:
    def __init__(self) -> None:
        self._batches: dict[str, DraftBatchRecord] = {}

    async def save_batch(self, batch: DraftBatchRecord) -> None:
        self._batches[batch.batch_id] = self._copy_batch(batch)

    async def find_post(self, post_id: str) -> tuple[DraftBatchRecord, DraftPostRecord] | None:
        for batch in self._batches.values():
            for post in batch.posts:
                if post.post_id == post_id:
                    return self._copy_batch(batch), deepcopy(post)
        return None

    async def get_batch(self, batch_id: str) -> DraftBatchRecord | None:
        batch = self._batches.get(batch_id)
        return self._copy_batch(batch) if batch is not None else None

    async def load_batches(self) -> list[DraftBatchRecord]:
        return [self._copy_batch(batch) for batch in self._batches.values()]

    async def update_post(
        self,
        post_id: str,
        *,
        artifact_type: str | object = _UNSET,
        artifact_uri: str | None | object = _UNSET,
        artifact_preview_uri: str | None | object = _UNSET,
        artifact_mime_type: str | None | object = _UNSET,
        artifact_metadata: dict | object = _UNSET,
        artifact_generation_status: str | object = _UNSET,
        artifact_job_id: str | None | object = _UNSET,
        generated_artifacts: list | object = _UNSET,
        review_status: str | object = _UNSET,
        approval_id: str | None | object = _UNSET,
        credential_ref: str | None | object = _UNSET,
        execution_status: str | object = _UNSET,
        visibility: str | object = _UNSET,
        public_release_requested: bool | object = _UNSET,
        scheduled_at: datetime | None | object = _UNSET,
        attempts: int | object = _UNSET,
        last_error: str | None | object = _UNSET,
        provider_post_id: str | None | object = _UNSET,
        provider_post_url: str | None | object = _UNSET,
    ) -> bool:
        for batch in self._batches.values():
            for post in batch.posts:
                if post.post_id != post_id:
                    continue

                if artifact_type is not _UNSET:
                    post.artifact_type = artifact_type
                if artifact_uri is not _UNSET:
                    post.artifact_uri = artifact_uri
                if artifact_preview_uri is not _UNSET:
                    post.artifact_preview_uri = artifact_preview_uri
                if artifact_mime_type is not _UNSET:
                    post.artifact_mime_type = artifact_mime_type
                if artifact_metadata is not _UNSET:
                    post.artifact_metadata = artifact_metadata
                if artifact_generation_status is not _UNSET:
                    post.artifact_generation_status = artifact_generation_status
                if artifact_job_id is not _UNSET:
                    post.artifact_job_id = artifact_job_id
                if generated_artifacts is not _UNSET:
                    post.generated_artifacts = generated_artifacts
                if review_status is not _UNSET:
                    post.review_status = review_status
                if approval_id is not _UNSET:
                    post.approval_id = approval_id
                if credential_ref is not _UNSET:
                    post.credential_ref = credential_ref
                if execution_status is not _UNSET:
                    post.execution_status = execution_status
                if visibility is not _UNSET:
                    post.visibility = visibility
                if public_release_requested is not _UNSET:
                    post.public_release_requested = public_release_requested
                if scheduled_at is not _UNSET:
                    post.scheduled_at = scheduled_at
                if attempts is not _UNSET:
                    post.attempts = attempts
                if last_error is not _UNSET:
                    post.last_error = last_error
                if provider_post_id is not _UNSET:
                    post.provider_post_id = provider_post_id
                if provider_post_url is not _UNSET:
                    post.provider_post_url = provider_post_url

                self._sync_batch_status(batch)
                return True

        return False

    @staticmethod
    def _copy_batch(batch: DraftBatchRecord) -> DraftBatchRecord:
        return DraftBatchRecord.model_validate(batch.model_dump(mode="python"))

    @staticmethod
    def _sync_batch_status(batch: DraftBatchRecord) -> None:
        statuses = [post.review_status for post in batch.posts]
        if statuses and all(status == "approved" for status in statuses):
            batch.status = "approved"
        elif any(status == "changes_requested" for status in statuses):
            batch.status = "changes_requested"
        elif any(status == "rejected" for status in statuses):
            batch.status = "rejected"
        else:
            batch.status = "pending_review"


@pytest.fixture
def in_memory_marketing_draft_store(monkeypatch: pytest.MonkeyPatch):
    from main import app
    import api.v1.marketing_drafts as marketing_drafts_module
    import services.marketing_scheduler as marketing_scheduler_module
    import services.content_creator_service as content_creator_service_module
    from core.database import get_db_session, get_read_db_session

    store = _InMemoryDraftBatchStore()

    class FakeDraftBatchStore:
        def __init__(self, _session) -> None:
            self._store = store

        async def save_batch(self, batch: DraftBatchRecord) -> None:
            await self._store.save_batch(batch)

        async def find_post(self, post_id: str) -> tuple[DraftBatchRecord, DraftPostRecord] | None:
            return await self._store.find_post(post_id)

        async def get_batch(self, batch_id: str) -> DraftBatchRecord | None:
            return await self._store.get_batch(batch_id)

        async def load_batches(self) -> list[DraftBatchRecord]:
            return await self._store.load_batches()

        async def update_post(self, post_id: str, **kwargs):
            return await self._store.update_post(post_id, **kwargs)

    async def _fake_db_session():
        yield _DummyAsyncSession()

    monkeypatch.setattr(marketing_drafts_module, "DatabaseDraftBatchStore", FakeDraftBatchStore)
    monkeypatch.setattr(marketing_scheduler_module, "DatabaseDraftBatchStore", FakeDraftBatchStore)
    monkeypatch.setattr(content_creator_service_module, "DatabaseDraftBatchStore", FakeDraftBatchStore)
    app.dependency_overrides[get_db_session] = _fake_db_session
    app.dependency_overrides[get_read_db_session] = _fake_db_session

    try:
        yield store
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_read_db_session, None)


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

    Applies all migrations to head to ensure coverage of latest schema changes.
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
        conn.execute(text(
            "CREATE TABLE alembic_version (version_num VARCHAR(255) NOT NULL PRIMARY KEY)"
        ))
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

    # Apply all migrations to head (updated for AGP1-DB-0.2)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def migrated_db(test_db_url: str) -> None:
    """Apply migrations once per pytest session, but only when requested.

    This keeps `pytest tests/` (unit-style suites) free of DB requirements.
    Integration tests that use the DB should request `async_engine`/`async_session`.
    """

    _apply_alembic_migrations(test_db_url)


@pytest.fixture
async def async_engine(test_db_url: str, migrated_db):
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
