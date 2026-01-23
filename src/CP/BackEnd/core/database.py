"""
Database configuration and session management for CP Backend
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import asyncio

from core.config import settings

# Declarative base for all models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.DEBUG,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: Database session (auto-closed after request)
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize database - create all tables.
    
    Should be called at application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def retry_async(func, retries: int = 3, delay: int = 1):
    """
    Retry a function with exponential backoff.

    Args:
        func: The function to retry.
        retries: Number of retry attempts.
        delay: Initial delay in seconds.
    
    Returns:
        Result of the function call.
    
    Raises:
        Exception: If all retries fail.
    """
    for attempt in range(retries):
        try:
            return await func()
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise e
