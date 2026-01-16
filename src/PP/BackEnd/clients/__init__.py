"""
PP Backend Clients Package
HTTP clients for external services (Plant API, etc.)
"""

from .plant_client import (
    PlantAPIClient,
    get_plant_client,
    close_plant_client,
    PlantAPIError,
    ConstitutionalAlignmentError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    SkillCreate,
    SkillResponse,
    JobRoleCreate,
    JobRoleResponse,
    AgentCreate,
    AgentResponse,
    ErrorResponse,
)

__all__ = [
    "PlantAPIClient",
    "get_plant_client",
    "close_plant_client",
    "PlantAPIError",
    "ConstitutionalAlignmentError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    "SkillCreate",
    "SkillResponse",
    "JobRoleCreate",
    "JobRoleResponse",
    "AgentCreate",
    "AgentResponse",
    "ErrorResponse",
]
