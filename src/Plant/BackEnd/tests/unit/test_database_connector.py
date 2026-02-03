import asyncio
from typing import Any, Callable, Optional

import pytest


class FakeConn:
    def __init__(self, fail_on_sql_contains: Optional[str] = None):
        self.fail_on_sql_contains = fail_on_sql_contains
        self.executed: list[str] = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, stmt: Any) -> None:
        sql = str(getattr(stmt, "text", stmt))
        self.executed.append(sql)
        if self.fail_on_sql_contains and self.fail_on_sql_contains in sql:
            raise RuntimeError("extension not available")

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class _AsyncCtx:
    def __init__(self, conn: FakeConn):
        self._conn = conn

    async def __aenter__(self) -> FakeConn:
        return self._conn

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeEngine:
    def __init__(self, conn: FakeConn, dispose_raises: bool = False):
        self._conn = conn
        self._dispose_raises = dispose_raises
        self.disposed = 0

    def connect(self) -> _AsyncCtx:
        return _AsyncCtx(self._conn)

    async def dispose(self) -> None:
        self.disposed += 1
        if self._dispose_raises:
            raise RuntimeError("dispose failed")


def _fake_session_factory() -> Callable[[], Any]:
    class FakeSession:
        def __init__(self):
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    return FakeSession


@pytest.mark.asyncio
async def test_database_connector_initialize_sets_up_engine_and_extensions(monkeypatch):
    from core import database as db

    conn = FakeConn()
    engine = FakeEngine(conn)

    monkeypatch.setattr(db, "create_async_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *args, **kwargs: _fake_session_factory())

    connector = db.DatabaseConnector()
    await connector.initialize()

    assert connector.engine is engine
    assert connector.async_session_factory is not None
    assert connector._initialized is True

    # _setup_extensions always sets search_path
    assert any("SET search_path" in s for s in conn.executed)


@pytest.mark.asyncio
async def test_setup_extensions_rolls_back_when_extension_missing(monkeypatch):
    from core import database as db

    conn = FakeConn(fail_on_sql_contains="vector")
    engine = FakeEngine(conn)

    monkeypatch.setattr(db, "create_async_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *args, **kwargs: _fake_session_factory())

    connector = db.DatabaseConnector()
    await connector.initialize()

    # vector extension failure should roll back but still continue
    assert conn.rollbacks >= 1
    assert any("CREATE EXTENSION IF NOT EXISTS vector" in s for s in conn.executed)


@pytest.mark.asyncio
async def test_initialize_recreates_engine_when_event_loop_changes(monkeypatch):
    from core import database as db

    first_conn = FakeConn()
    first_engine = FakeEngine(first_conn)

    second_conn = FakeConn()
    second_engine = FakeEngine(second_conn)

    engines = [first_engine, second_engine]

    def fake_create_async_engine(*args, **kwargs):
        return engines.pop(0)

    monkeypatch.setattr(db, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *args, **kwargs: _fake_session_factory())

    connector = db.DatabaseConnector()
    await connector.initialize()

    # Simulate a different event loop by setting _engine_loop to a non-equal object
    connector._initialized = True
    connector._engine_loop = object()

    await connector.initialize()

    assert connector.engine is second_engine
    assert first_engine.disposed == 1


@pytest.mark.asyncio
async def test_get_db_session_yields_and_closes_session(monkeypatch):
    from core import database as db

    conn = FakeConn()
    engine = FakeEngine(conn)

    monkeypatch.setattr(db, "create_async_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *args, **kwargs: _fake_session_factory())

    # Replace the module singleton so get_db_session uses our fake connector
    connector = db.DatabaseConnector()
    monkeypatch.setattr(db, "_connector", connector)

    agen = db.get_db_session()
    session = await agen.__anext__()
    assert hasattr(session, "close")

    await agen.aclose()


@pytest.mark.asyncio
async def test_health_check_returns_false_on_exception(monkeypatch):
    from core import database as db

    class BadEngine(FakeEngine):
        def connect(self) -> _AsyncCtx:
            raise RuntimeError("no connect")

    engine = BadEngine(FakeConn())

    monkeypatch.setattr(db, "create_async_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr(db, "async_sessionmaker", lambda *args, **kwargs: _fake_session_factory())

    connector = db.DatabaseConnector()
    ok = await connector.health_check()
    assert ok is False
