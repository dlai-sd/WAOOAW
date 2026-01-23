"""
Database configuration and session management for CP Backend
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
from core.logging import get_logger  # Importing logger

from core.config import settings
import asyncio

# Initialize logger
logger = get_logger(__name__)

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
    await retry_on_transient_errors(_init_db_internal)


async def _init_db_internal():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def retry_on_transient_errors(func, *args):
    """
    Retry a function call with exponential backoff for transient errors.
    
    Args:
        func: Function to call
        *args: Arguments for the function
            
    Returns:
        Result of the function call
            
    Raises:
        Exception: If all retries fail
    """
    retries = 3
    for attempt in range(retries):
        try:
            return await func(*args)
        except SQLAlchemyError as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Transient error: {e}. Retrying in {wait_time}s...", extra={"attempt": attempt + 1})
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All retries failed for {func.__name__}: {e}")
                raise
