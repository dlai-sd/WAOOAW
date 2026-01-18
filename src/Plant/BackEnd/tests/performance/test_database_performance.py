"""
Performance/Load Tests: Database Operations Benchmarks

Tests database performance under load using pytest-benchmark.
Validates:
- Query performance (SELECT, INSERT, UPDATE)
- Bulk operations throughput
- Connection pool efficiency
- Index utilization

Note: pytest-benchmark doesn't support async functions directly,
so we use synchronous wrappers with asyncio.run() for database operations.
"""

import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import asyncio
import uuid

from models.skill import Skill
from models.base_entity import BaseEntity


# Helper to run async functions in benchmark
def run_async(coro):
    """Helper to run async coroutine in benchmark."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture(scope="module")
def sync_db_url():
    """Database URL for performance tests."""
    import os
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev"
    )


def test_single_entity_insert_performance(benchmark, sync_db_url):
    """Benchmark single entity INSERT performance."""
    
    async def insert_skill():
        engine = create_async_engine(sync_db_url, echo=False)
        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            skill = Skill(
                name=f"Benchmark_Skill_{uuid.uuid4()}",
                description="Performance test skill",
                category="technical",
                entity_type="Skill",
                governance_agent_id="genesis",
                version_hash="benchmark_v1",
                hash_chain_sha256=["hash1"],
            )
            session.add(skill)
            await session.flush()
            skill_id = skill.id
            await session.rollback()
        
        await engine.dispose()
        return skill_id
    
    # Benchmark the insert
    result = benchmark(lambda: run_async(insert_skill()))
    assert result is not None


def test_bulk_insert_performance(benchmark, sync_db_url):
    """Benchmark bulk INSERT operations (100 entities)."""
    
    async def bulk_insert():
        engine = create_async_engine(sync_db_url, echo=False)
        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            skills = [
                Skill(
                    name=f"BulkSkill_{uuid.uuid4()}_{i}",
                    description=f"Bulk test skill {i}",
                    category="technical",
                    entity_type="Skill",
                    governance_agent_id="genesis",
                    version_hash=f"bulk_v{i}",
                    hash_chain_sha256=[f"hash{i}"],
                )
                for i in range(100)
            ]
            session.add_all(skills)
            await session.flush()
            count = len(skills)
            await session.rollback()
        
        await engine.dispose()
        return count
    
    result = benchmark(lambda: run_async(bulk_insert()))
    assert result == 100


def test_query_by_id_performance(benchmark, sync_db_url):
    """Benchmark SELECT by primary key (indexed)."""
    
    async def setup_and_query():
        engine = create_async_engine(sync_db_url, echo=False)
        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            # Create test skill
            skill = Skill(
                name=f"QueryBenchmarkSkill_{uuid.uuid4()}",
                description="For query testing",
                category="technical",
                entity_type="Skill",
                governance_agent_id="genesis",
                version_hash="query_v1",
                hash_chain_sha256=["hash1"],
            )
            session.add(skill)
            await session.flush()
            skill_id = skill.id
            
            # Query it
            result = await session.get(Skill, skill_id)
            name = result.name if result else None
            
            await session.rollback()
        
        await engine.dispose()
        return name
    
    result = benchmark(lambda: run_async(setup_and_query()))
    assert result is not None


def test_query_with_filter_performance(benchmark, sync_db_url):
    """Benchmark SELECT with WHERE clause."""
    
    async def query_with_filter():
        engine = create_async_engine(sync_db_url, echo=False)
        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            stmt = select(Skill).where(Skill.category == "technical").limit(10)
            result = await session.execute(stmt)
            skills = result.scalars().all()
            count = len(skills)
        
        await engine.dispose()
        return count
    
    result = benchmark(lambda: run_async(query_with_filter()))
    assert result >= 0


def test_concurrent_reads_performance(benchmark, sync_db_url):
    """Benchmark concurrent read operations (10 parallel queries)."""
    
    async def concurrent_reads():
        engine = create_async_engine(sync_db_url, echo=False, pool_size=20)
        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async def single_read():
            async with async_session_maker() as session:
                stmt = select(Skill).limit(5)
                result = await session.execute(stmt)
                return result.scalars().all()
        
        tasks = [single_read() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        await engine.dispose()
        return len(results)
    
    result = benchmark(lambda: run_async(concurrent_reads()))
    assert result == 10


def test_entity_validation_performance(benchmark):
    """Benchmark entity validation (L0/L1 checks)."""
    
    def validate_entity():
        skill = Skill(
            name="ValidationBenchmark",
            description="Test validation performance",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="val_v1",
            hash_chain_sha256=["hash1"],
        )
        result = skill.validate_self()
        return result["compliant"]
    
    result = benchmark(validate_entity)
    assert result is True


def test_hash_chain_computation_performance(benchmark):
    """Benchmark SHA-256 hash chain computation."""
    
    from security.hash_chain import create_hash_link
    
    def compute_hash_chain():
        previous_hash = ""
        for i in range(10):
            data = f"amendment_{i}"
            new_hash = create_hash_link(previous_hash, data)
            previous_hash = new_hash
        return previous_hash
    
    result = benchmark(compute_hash_chain)
    assert result is not None
    assert len(result) == 64  # SHA-256 hex digest length


def test_cryptography_signing_performance(benchmark):
    """Benchmark RSA signing performance."""
    
    from security.cryptography import generate_rsa_keypair, sign_data
    
    private_key, _ = generate_rsa_keypair()
    data = "Performance test data for signing"
    
    def sign_operation():
        signature = sign_data(data, private_key)
        return signature
    
    result = benchmark(sign_operation)
    assert result is not None
    assert len(result) > 0


def test_cryptography_verification_performance(benchmark):
    """Benchmark RSA signature verification performance."""
    
    from security.cryptography import generate_rsa_keypair, sign_data, verify_signature
    
    private_key, public_key = generate_rsa_keypair()
    data = "Performance test data for verification"
    signature = sign_data(data, private_key)
    
    def verify_operation():
        is_valid = verify_signature(data, signature, public_key)
        return is_valid
    
    result = benchmark(verify_operation)
    assert result is True
