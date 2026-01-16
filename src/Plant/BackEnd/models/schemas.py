"""
Pydantic schemas for API request/response contracts
Separate from ORM models to maintain API stability
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ========== SKILL SCHEMAS ==========

class SkillBase(BaseModel):
    """Base skill schema with common fields."""
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    category: str = Field(..., description="Skill category (technical, soft_skill, domain_expertise)")


class SkillCreate(SkillBase):
    """Create skill request schema."""
    governance_agent_id: str = Field(default="genesis", description="Governance agent ID (genesis or governor UUID)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python 3.11",
                "description": "Modern Python programming with async/await, type hints, and FastAPI framework",
                "category": "technical",
                "governance_agent_id": "genesis"
            }
        }


class SkillUpdate(BaseModel):
    """Update skill request schema."""
    description: Optional[str] = None
    category: Optional[str] = None


class SkillResponse(SkillBase):
    """Skill response schema (for GET)."""
    id: UUID
    entity_type: str
    created_at: datetime
    updated_at: datetime
    status: str
    l0_compliance_status: Dict[str, bool]
    amendment_alignment: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Python 3.11",
                "description": "Modern Python programming with async/await, type hints, and FastAPI framework",
                "category": "technical",
                "entity_type": "skill",
                "created_at": "2026-01-16T10:30:00Z",
                "updated_at": "2026-01-16T10:30:00Z",
                "status": "certified",
                "l0_compliance_status": {
                    "L0-01": True,
                    "L0-02": True,
                    "L0-05": True
                },
                "amendment_alignment": "compliant"
            }
        }


# ========== JOBROLE SCHEMAS ==========

class JobRoleBase(BaseModel):
    """Base job role schema."""
    name: str = Field(..., description="Job role name")
    description: str = Field(..., description="Job role description")
    required_skills: List[UUID] = Field(..., description="Required skill IDs")
    seniority_level: str = Field(default="mid", description="Seniority level")


class JobRoleCreate(JobRoleBase):
    """Create job role request schema."""
    governance_agent_id: str = Field(default="genesis")


class JobRoleResponse(JobRoleBase):
    """Job role response schema."""
    id: UUID
    entity_type: str
    created_at: datetime
    updated_at: datetime
    status: str
    
    class Config:
        from_attributes = True


# ========== TEAM SCHEMAS ==========

class TeamCreate(BaseModel):
    """Create team request schema."""
    name: str
    description: str
    job_role_id: UUID
    governance_agent_id: str = Field(default="genesis")


class TeamResponse(BaseModel):
    """Team response schema."""
    id: UUID
    name: str
    description: str
    agents: List[UUID]
    job_role_id: UUID
    status: str
    
    class Config:
        from_attributes = True


# ========== AGENT SCHEMAS ==========

class AgentCreate(BaseModel):
    """Create agent request schema."""
    name: str = Field(..., description="Agent display name")
    skill_id: UUID = Field(..., description="Certified skill UUID")
    job_role_id: UUID = Field(..., description="Certified job role UUID")
    team_id: Optional[UUID] = Field(None, description="Team UUID (optional)")
    industry_id: UUID = Field(..., description="Industry UUID (immutable after creation)")
    governance_agent_id: str = Field(default="genesis", description="Governance agent ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Email Marketing Agent",
                "skill_id": "550e8400-e29b-41d4-a716-446655440000",
                "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
                "industry_id": "770e8400-e29b-41d4-a716-446655440002",
                "governance_agent_id": "genesis"
            }
        }


class AgentResponse(BaseModel):
    """Agent response schema."""
    id: UUID
    name: str
    skill_id: UUID
    job_role_id: UUID
    team_id: Optional[UUID]
    industry_id: UUID
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "name": "Email Marketing Agent",
                "skill_id": "550e8400-e29b-41d4-a716-446655440000",
                "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
                "team_id": None,
                "industry_id": "770e8400-e29b-41d4-a716-446655440002",
                "status": "active",
                "created_at": "2026-01-16T10:30:00Z"
            }
        }


# ========== GENERIC SCHEMAS ==========

class BaseEntitySchema(BaseModel):
    """Generic base entity schema."""
    id: UUID
    entity_type: str
    created_at: datetime
    updated_at: datetime
    status: str
    l0_compliance_status: Dict[str, Any]
    amendment_history: List[Dict[str, Any]]
    governance_agent_id: str
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    error_code: str
    timestamp: datetime


class ValidationResult(BaseModel):
    """Validation result schema."""
    compliant: bool
    checks: Dict[str, bool]
    violations: List[str]
