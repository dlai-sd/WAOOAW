"""
SQLAlchemy database setup
Engine, session factory, and base class for ORM models
"""

from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
    connect_args={"connect_timeout": 10},
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for all models
Base = declarative_base()


@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """
    Enable foreign keys and execute RLS setup on connection.
    
    Args:
        dbapi_connection: Raw database connection
        connection_record: SQLAlchemy connection record
    """
    cursor = dbapi_connection.cursor()
    # Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    # Enable UUID extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp;")
    # Set default search path
    cursor.execute("SET search_path TO public;")
    cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session.
    
    Yields:
        Session: Database session (auto-closed after use)
        
    Example:
        @app.get("/items/")
        async def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables.
    
    This should be called once at application startup.
    For production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
