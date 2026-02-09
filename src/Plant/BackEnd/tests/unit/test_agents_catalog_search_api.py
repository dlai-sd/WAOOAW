import pytest

from api.v1.agents import list_agents


class _DummyResult:
    def mappings(self):
        return self

    def all(self):
        return []


class _DummyDB:
    def __init__(self):
        self.last_stmt = None

    async def execute(self, stmt):
        self.last_stmt = stmt
        return _DummyResult()


@pytest.mark.asyncio
async def test_list_agents_adds_q_search_predicates():
    db = _DummyDB()
    await list_agents(q="email", db=db)

    rendered = str(db.last_stmt)
    assert "lower(" in rendered
    assert " like " in rendered.lower()


@pytest.mark.asyncio
async def test_list_agents_without_q_does_not_add_like_filters():
    db = _DummyDB()
    await list_agents(db=db)

    rendered = str(db.last_stmt).lower()
    assert " like " not in rendered
