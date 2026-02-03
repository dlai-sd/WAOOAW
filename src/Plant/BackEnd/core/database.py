"""
SQLAlchemy Async Database Connector (Global DB Abstraction Layer)
Async-first connection pooling with environment awareness, Cloud SQL Proxy integration,
and FastAPI dependency injection.

Reference: docs/plant/PLANT_BLUEPRINT.yaml (database_connector section)
Pattern: Global Connector with Dependency Injection + Connection Pooling
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event, text

from core.config import settings

# Declarative base for all models (inherits to all entity models)
Base = declarative_base()

# Logger for database operations
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Global database connector managing async SQLAlchemy engine and session factory.
    
    Features:
    - Environment-aware: Picks database URL from .env based on ENVIRONMENT
    - Async-first: Uses asyncpg driver for non-blocking I/O
    - Connection pooling: Configurable per environment (local/demo/uat/prod)
    - Cloud SQL Proxy: Unix socket support (/cloudsql/PROJECT:REGION:instance)
    - Extension auto-loading: pgvector, uuid-ossp loaded on first connection
    - Dependency injection: FastAPI Depends() compatible
    
    Example:
        connector = DatabaseConnector()
        async with connector.get_session() as session:
            result = await session.execute(select(Skill))
            skills = result.scalars().all()
    """
    
    def __init__(self):
        """Initialize database connector with async engine and session factory."""
        self.engine = None
        self.async_session_factory = None
        self._initialized = False
        self._init_lock: Optional[asyncio.Lock] = None
        self._lock_loop: Optional[asyncio.AbstractEventLoop] = None
        self._engine_loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def initialize(self):
        """
        Initialize async engine and session factory.
        Should be called at application startup.
        
        Example:
            @app.on_event("startup")
            async def startup():
                await connector.initialize()
        """
        loop = asyncio.get_running_loop()

        # pytest-asyncio (and some runtimes) can create/close a new event loop per test.
        # If the engine was created in a different loop, dispose/reset so we don't reuse
        # connections tied to a closed loop.
        if self._initialized and self._engine_loop is not None and self._engine_loop is not loop:
            try:
                if self.engine is not None:
                    await self.engine.dispose()
            except Exception:
                # Best-effort: disposing an engine created on a closed loop may fail.
                pass

            self.engine = None
            self.async_session_factory = None
            self._initialized = False
            self._engine_loop = None

        if self._init_lock is None or self._lock_loop is not loop:
            self._init_lock = asyncio.Lock()
            self._lock_loop = loop

        async with self._init_lock:
            if self._initialized:
                return

            # Create async engine with connection pooling
            self.engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_pre_ping=settings.database_pool_pre_ping,
                echo=settings.database_echo,
                connect_args={
                    "timeout": 10,
                    "command_timeout": 30,
                    "server_settings": {
                        "application_name": "plant_backend",
                        "jit": "off",
                    },
                },
            )

            # Create async session factory
            self.async_session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Setup connection event listeners / extensions
            await self._setup_extensions()

            self._initialized = True
            self._engine_loop = loop
    
    async def _setup_extensions(self):
        """Load PostgreSQL extensions on connection."""
        # Use connect() instead of begin() to avoid automatic transaction
        async with self.engine.connect() as conn:
            # Try pgvector extension
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.commit()
                logger.info("pgvector extension enabled")
            except Exception as e:
                # Extension not available - log and continue
                logger.info(f"pgvector extension not available (okay for local dev): {type(e).__name__}")
                await conn.rollback()
            
            # Try uuid-ossp extension
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
                await conn.commit()
                logger.info("uuid-ossp extension enabled")
            except Exception as e:
                logger.info(f"uuid-ossp extension not available: {type(e).__name__}")
                await conn.rollback()
            
            # Set default search path
            await conn.execute(text("SET search_path TO public;"))
    
    async def get_session(self) -> AsyncSession:
        """
        Get a new async database session (context manager).
        
        Returns:
            AsyncSession: Database session (auto-closed)
            
        Example:
            async with connector.get_session() as session:
                result = await session.execute(select(Skill))
        """
        # Always call initialize() so it can detect a changed/closed event loop
        # and recreate the engine if needed (common under pytest-asyncio).
        await self.initialize()
        return self.async_session_factory()
    
    async def close(self):
        """
        Close all connections in the pool.
        Should be called at application shutdown.
        
        Example:
            @app.on_event("shutdown")
            async def shutdown():
                await connector.close()
        """
        if self.engine is not None:
            try:
                await self.engine.dispose()
            finally:
                self.engine = None
                self.async_session_factory = None
                self._initialized = False
                self._engine_loop = None
    
    async def health_check(self) -> bool:
        """
        Check database connectivity and pool health.
        
        Returns:
            bool: True if database is reachable, False otherwise
            
        Example:
            if await connector.health_check():
                print("Database is healthy")
        """
        try:
            if self.engine is None:
                await self.initialize()

            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Global connector instance (singleton)
_connector = DatabaseConnector()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for injecting async database sessions.
    Session is automatically closed after request completes.
    
    Usage in FastAPI endpoints:
        @app.get("/skills/")
        async def list_skills(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(Skill))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session (auto-closed)
    """
    # Always initialize: under pytest-asyncio a new loop may be created per test,
    # and we must not reuse an engine/pool bound to a closed loop.
    await _connector.initialize()
    
    session = _connector.async_session_factory()
    try:
        yield session
    finally:
        await session.close()


# Alias for backwards compatibility
get_db = get_db_session


async def initialize_database():
    """
    Initialize database connector at application startup.
    
    Should be called in FastAPI startup event:
        @app.on_event("startup")
        async def startup():
            await initialize_database()
    """
    await _connector.initialize()


async def shutdown_database():
    """
    Shutdown database connector at application shutdown.
    
    Should be called in FastAPI shutdown event:
        @app.on_event("shutdown")
        async def shutdown():
            await shutdown_database()
    """
    await _connector.close()


async def health_check_database() -> bool:
    """
    Health check endpoint for database connectivity.
    
    Returns:
        bool: True if database is healthy
        
    Usage:
        @app.get("/health/db")
        async def db_health():
            healthy = await health_check_database()
            return {"database": "healthy" if healthy else "unhealthy"}
    """
    return await _connector.health_check()


def get_connector() -> DatabaseConnector:
    """
    Get global database connector instance.
    
    Returns:
        DatabaseConnector: Global singleton instance
    """
    return _connector

# Module-level convenience exports for backward compatibility
def get_engine():
    """Get the async engine from connector"""
    return _connector.engine

# For synchronous operations (use sparingly - prefer async)
engine = _connector.engine  # This will be None until initialized


def SessionLocal():
    """Get the async session factory from connector"""
    return _connector.async_session_factory

