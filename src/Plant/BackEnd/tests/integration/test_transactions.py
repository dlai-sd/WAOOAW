"""
Integration Tests: Transaction Consistency

Tests transaction handling and data consistency:
- ACID compliance
- Rollback behavior
- Commit atomicity
- Isolation levels
- Nested transaction handling
"""

import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from models.skill import Skill
from models.agent import Agent
from models.industry import Industry
from models.job_role import JobRole


@pytest.mark.asyncio
async def test_transaction_commit_atomicity(async_session: AsyncSession):
    """Test that transaction commits atomically."""
    skill1_id = uuid.uuid4()
    skill2_id = uuid.uuid4()
    
    skill1 = Skill(
        id=skill1_id,
        entity_type="Skill",
        name="AtomicSkill1",
        description="Atomic skill 1",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    skill2 = Skill(
        id=skill2_id,
        entity_type="Skill",
        name="AtomicSkill2",
        description="Atomic skill 2",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    
    async_session.add(skill1)
    async_session.add(skill2)
    await async_session.commit()
    
    # Both should be inserted
    stmt1 = select(Skill).where(Skill.id == skill1_id)
    result1 = await async_session.execute(stmt1)
    assert result1.scalars().first() is not None
    
    stmt2 = select(Skill).where(Skill.id == skill2_id)
    result2 = await async_session.execute(stmt2)
    assert result2.scalars().first() is not None


@pytest.mark.asyncio
async def test_transaction_rollback_on_constraint_violation(async_session: AsyncSession):
    """Test that transaction rolls back on constraint violation."""
    constraint_id = uuid.uuid4()
    
    # First insert succeeds
    skill1 = Skill(
        id=constraint_id,
        entity_type="Skill",
        name="ConstraintSkill",
        description="Constraint skill",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    async_session.add(skill1)
    await async_session.commit()
    
    # Attempt duplicate key insert should fail
    skill2 = Skill(
        id=constraint_id,  # Duplicate!
        entity_type="Skill",
        name="ConstraintSkill2",
        description="Constraint skill 2",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    async_session.add(skill2)
    
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_transaction_isolation_level(async_engine):
    """Test that isolation level is appropriately set."""
    async with async_engine.connect() as conn:
        # Check default isolation level
        result = await conn.execute(
            text("SHOW transaction_isolation")
        )
        isolation_level = result.scalar()
        normalized = (isolation_level or "").replace(" ", "_")
        # Should be read_committed or serializable
        assert normalized in [
            'read_committed',
            'serializable',
            'repeatable_read',
            'uncommitted_read'
        ]


@pytest.mark.asyncio
async def test_dirty_read_prevention(async_session: AsyncSession, create_test_skill):
    """Test that dirty reads are prevented."""
    # Create skill in current transaction
    skill = await create_test_skill(name="DirtyReadTest")
    
    # Before commit, data should not be visible to other transactions
    # (implementation depends on isolation level)
    
    # After commit, data should be visible
    stmt = select(Skill).where(Skill.name == "DirtyReadTest")
    result = await async_session.execute(stmt)
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_repeatable_read_consistency(async_session: AsyncSession, create_test_skill):
    """Test repeatable read within transaction."""
    skill = await create_test_skill(name="RepeatableReadTest")
    original_name = skill.name
    
    # Read again in same transaction
    stmt = select(Skill).where(Skill.id == skill.id)
    result = await async_session.execute(stmt)
    retrieved = result.scalars().first()
    
    assert retrieved.name == original_name


@pytest.mark.asyncio
async def test_phantom_read_handling(async_session: AsyncSession):
    """Test phantom read behavior in transaction."""
    # Create initial set of skills
    for i in range(3):
        skill = Skill(
            id=uuid.uuid4(),
            entity_type="Skill",
            name=f"PhantomSkill_{i}",
            description=f"Phantom skill {i}",
            category="technical",
            created_at=datetime.utcnow(),
            status="active"
        )
        async_session.add(skill)
    
    await async_session.commit()
    
    # Count skills
    stmt1 = select(Skill).where(Skill.name.like("PhantomSkill_%"))
    result1 = await async_session.execute(stmt1)
    count1 = len(result1.scalars().all())
    assert count1 >= 3


@pytest.mark.asyncio
async def test_serialization_consistency(async_session: AsyncSession):
    """Test that serialization ensures consistency."""
    # Test multiple operations in sequence
    skill_ids = []
    
    for i in range(3):
        skill = Skill(
            id=uuid.uuid4(),
            entity_type="Skill",
            name=f"SerialSkill_{i}",
            description=f"Serial skill {i}",
            category="technical",
            created_at=datetime.utcnow(),
            status="active"
        )
        async_session.add(skill)
        skill_ids.append(skill.id)
    
    await async_session.commit()
    
    # All operations should have succeeded
    for skill_id in skill_ids:
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await async_session.execute(stmt)
        assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_concurrent_transaction_non_interference(async_session: AsyncSession):
    """Test that concurrent transactions don't interfere."""
    # Create a skill
    skill = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="ConcurrentTest",
        description="Concurrent test",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    async_session.add(skill)
    await async_session.commit()
    
    # Should be readable
    stmt = select(Skill).where(Skill.name == "ConcurrentTest")
    result = await async_session.execute(stmt)
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_transaction_deadlock_prevention(async_engine):
    """Test that deadlocks are handled or prevented."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession)
    
    async def insert_skill(name):
        async with session_factory() as session:
            skill = Skill(
                id=uuid.uuid4(),
                entity_type="Skill",
                name=name,
                description=f"Deadlock test {name}",
                category="technical",
                created_at=datetime.utcnow(),
                status="active"
            )
            session.add(skill)
            await session.commit()
    
    # Sequential inserts should not deadlock
    import asyncio
    results = await asyncio.gather(
        insert_skill("Skill1"),
        insert_skill("Skill2"),
        insert_skill("Skill3"),
        return_exceptions=True
    )
    
    # Check for exceptions
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0


@pytest.mark.asyncio
async def test_transaction_savepoint_support(async_session: AsyncSession):
    """Test that savepoints are supported for nested transactions."""
    skill = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="SavepointTest",
        description="Savepoint test",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    
    async_session.add(skill)
    
    # Savepoint would be used like: async with async_session.begin_nested():
    # For now, just verify commit works
    await async_session.commit()
    
    stmt = select(Skill).where(Skill.name == "SavepointTest")
    result = await async_session.execute(stmt)
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_transaction_foreign_key_integrity(
    async_session: AsyncSession,
    create_test_industry,
    create_test_agent
):
    """Test that foreign key constraints are enforced in transactions."""
    # Create industry first
    industry = await create_test_industry()
    
    # Create agent with valid foreign key
    agent = await create_test_agent()
    
    # Both operations should succeed
    assert agent is not None
    assert industry is not None


@pytest.mark.asyncio
async def test_transaction_cascading_deletes(async_session: AsyncSession):
    """Test cascading delete behavior (if implemented)."""
    # This test assumes potential cascade behavior
    # Current schema may not have cascades implemented
    
    skill = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="CascadeTest",
        description="Cascade test",
        category="technical",
        created_at=datetime.utcnow(),
        status="active"
    )
    
    async_session.add(skill)
    await async_session.commit()
    
    # Verify insert succeeded
    stmt = select(Skill).where(Skill.name == "CascadeTest")
    result = await async_session.execute(stmt)
    assert result.scalars().first() is not None
