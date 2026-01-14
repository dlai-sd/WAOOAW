"""
Entity Validator - Business logic and uniqueness checks
"""

from typing import List


def validate_entity_uniqueness(entity_type: str, field_name: str, value: str, db_session) -> bool:
    """
    Check if entity field value is unique (no duplicates).
    
    Args:
        entity_type: Type of entity (Skill, JobRole, Team, Agent, Industry)
        field_name: Field to check uniqueness (usually 'name')
        value: Field value to check
        db_session: Database session
        
    Returns:
        bool: True if unique (no duplicate found)
        
    Example:
        >>> if not validate_entity_uniqueness("Skill", "name", "Python", db):
        ...     raise DuplicateEntityError("Skill with name 'Python' already exists")
    """
    
    # Map entity type to model class
    from models.skill import Skill
    from models.job_role import JobRole
    from models.team import Team
    from models.agent import Agent
    from models.industry import Industry
    
    model_map = {
        "Skill": Skill,
        "JobRole": JobRole,
        "Team": Team,
        "Agent": Agent,
        "Industry": Industry,
    }
    
    if entity_type not in model_map:
        return True  # Unknown type, assume valid
    
    Model = model_map[entity_type]
    
    # Query for existing entity with same field value
    existing = db_session.query(Model).filter(
        getattr(Model, field_name) == value,
        Model.status != "deleted"
    ).first()
    
    return existing is None  # True if no duplicate found
