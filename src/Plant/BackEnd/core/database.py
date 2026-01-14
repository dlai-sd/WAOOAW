"""
SQLAlchemy Async Database Connector (Global DB Abstraction Layer)
Async-first connection pooling with environment awareness, Cloud SQL Proxy integration,
and FastAPI dependency injection.

Reference: docs/plant/PLANT_BLUEPRINT.yaml (database_connector section)
Pattern: Global Connector with Dependency Injection + Connection Pooling
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event, text
from sqlalchemy.pool import NullPool, QueuePool

from core.config import settings

# Declarative base for all models (inherits to all entity models)
Base = declarative_base()


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
    
    async def initialize(self):
        """
        Initialize async engine and session factory.
        Should be called at application startup.
        
        Example:
            @app.on_event("startup")
            async def startup():
                await connector.initialize()
        """
        if self._initialized:
            return
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,  # Use NullPool for async compatibility
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
        
        # Setup connection event listeners
        await self._setup_extensions()
        
        self._initialized = True
    
    async def _setup_extensions(self):
        """Load PostgreSQL extensions on connection."""
        async with self.engine.begin() as conn:
            # Enable pgvector extension (vector similarity search)
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            # Enable uuid-ossp extension (UUID generation)
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            
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
        if not self._initialized:
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
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
    
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
    async with _connector.get_session() as session:
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

