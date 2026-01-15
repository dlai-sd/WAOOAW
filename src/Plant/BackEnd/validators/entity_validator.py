"""
Entity Validator - Business logic and uniqueness checks
"""

from typing import List
from sqlalchemy import select


async def validate_entity_uniqueness(db_session, Model, field_name: str, value: str) -> bool:
    """
    Check if entity field value is unique (no duplicates).
    
    Args:
        db_session: Async database session
        Model: SQLAlchemy model class
        field_name: Field to check uniqueness (usually 'name')
        value: Field value to check
        
    Returns:
        bool: True if unique (no duplicate found)
        
    Example:
        >>> from models.skill import Skill
        >>> if await validate_entity_uniqueness(db, Skill, "name", "Python"):
        ...     # Duplicate found
        ...     raise DuplicateEntityError("Skill with name 'Python' already exists")
    """
    # Query for existing entity with same field value
    stmt = select(Model).where(
        getattr(Model, field_name) == value,
        Model.status != "deleted"
    )
    result = await db_session.execute(stmt)
    existing = result.scalars().first()
    
    return existing  # Returns existing entity if found, None otherwise
