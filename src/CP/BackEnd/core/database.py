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
    
    Usage:
        @router.get("/users/")
        async def list_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
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
    
    For development only. Use Alembic migrations in production.
    
    Should be called at application startup:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def retry_with_exponential_backoff(func, *args, max_attempts=3):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        args: Arguments for the function
        max_attempts: Maximum number of attempts
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: If all attempts fail
    """
    for attempt in range(max_attempts):
        try:
            return await func(*args)
        except Exception as e:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                raise e
