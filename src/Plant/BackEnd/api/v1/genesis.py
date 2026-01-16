"""
Genesis certification endpoints - skills + job roles
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from models.schemas import SkillCreate, SkillResponse, JobRoleCreate, JobRoleResponse
from services.skill_service import SkillService
from services.job_role_service import JobRoleService
from core.exceptions import ConstitutionalAlignmentError, DuplicateEntityError, ValidationError


router = APIRouter(prefix="/genesis", tags=["genesis"])


# =====================
# SKILL ENDPOINTS
# =====================

@router.post("/skills", response_model=SkillResponse, status_code=201,
    summary="Create new skill",
    description="""
    Create a new skill entity pending Genesis certification.
    
    **Constitutional Validation:**
    - L0-01: governance_agent_id must be present (genesis or governor UUID)
    - L0-02: Skill must have unique name within category
    - L0-05: Amendment history initialized with creation event
    - L0-06: Version hash calculated from entity data
    
    **Workflow:**
    1. Validate constitutional alignment (L0/L1 principles)
    2. Check for duplicate skill (name + category uniqueness)
    3. Calculate version hash (SHA256 of entity data)
    4. Initialize amendment history with creation signature
    5. Store skill entity with status="pending_certification"
    6. Trigger Genesis certification workflow (multi-gate approval)
    
    **Returns:**
    - 201 Created: Skill entity with UUID and pending status
    - 409 Conflict: Duplicate skill already exists
    - 422 Unprocessable Entity: Constitutional alignment failure
    - 500 Internal Server Error: Unexpected error
    
    **Example Request:**
    ```json
    {
      "name": "Python 3.11",
      "description": "Modern Python programming",
      "category": "technical",
      "governance_agent_id": "genesis"
    }
    ```
    """,
    responses={
        201: {
            "description": "Skill created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Python 3.11",
                        "description": "Modern Python programming",
                        "category": "technical",
                        "status": "pending_certification",
                        "created_at": "2026-01-16T10:30:00Z"
                    }
                }
            }
        },
        409: {
            "description": "Duplicate skill already exists",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://waooaw.com/errors/duplicate-entity",
                        "title": "Duplicate Entity Error",
                        "status": 409,
                        "detail": "Skill 'Python 3.11' already exists in category 'technical'",
                        "instance": "/api/v1/genesis/skills"
                    }
                }
            }
        },
        422: {
            "description": "Constitutional alignment failure",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://waooaw.com/errors/constitutional-alignment",
                        "title": "Constitutional Alignment Error",
                        "status": 422,
                        "detail": "governance_agent_id required (L0-01: Single Governor)",
                        "violations": ["L0-01: governance_agent_id missing"]
                    }
                }
            }
        }
    }
)
async def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db)
):
    """
    Create new Skill with Genesis certification eligibility.
    
    - Validates constitutional alignment (L0/L1)
    - Checks uniqueness
    - Calculates version hash
    - Returns Skill entity
    """
    try:
        service = SkillService(db)
        skill = await service.create_skill(skill_data)
        return skill
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/skills", response_model=List[SkillResponse])
async def list_skills(
    category: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all skills with optional filtering.
    
    - Filter by category (technical/soft_skill/domain_expertise)
    - Pagination support
    """
    service = SkillService(db)
    skills = await service.list_skills(category=category, limit=limit, offset=offset)
    return skills


@router.get("/skills/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve Skill by ID.
    """
    service = SkillService(db)
    skill = await service.get_skill_by_id(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")
    
    return skill


@router.post("/skills/{skill_id}/certify", response_model=SkillResponse,
    summary="Certify skill via Genesis workflow",
    description="""
    Trigger Genesis certification workflow for a pending skill.
    
    **Authorization (Future):**
    - Requires Genesis role or Governor permission
    - JWT token validated at gateway layer
    
    **Constitutional Validation:**
    - L0-02: Skill must pass multi-gate certification
    - L0-05: Certification event added to audit trail
    - L0-06: Version hash updated after certification
    - L0-07: Amendment history includes certification signature
    
    **Workflow:**
    1. Validate skill exists and status="pending_certification"
    2. Run constitutional compliance checks (L0/L1)
    3. Trigger Temporal workflow for Genesis approval
    4. Update skill status="certified" after approval
    5. Sign amendment with Genesis agent key
    6. Emit certification event to audit log
    
    **Returns:**
    - 200 OK: Skill certified successfully
    - 404 Not Found: Skill doesn't exist
    - 422 Unprocessable Entity: Certification requirements not met
    - 500 Internal Server Error: Workflow failure
    
    **Example Request:**
    ```json
    {
      "certification_notes": "Skill validated by Genesis Agent",
      "approval_gate": "technical_review"
    }
    ```
    """,
    responses={
        200: {
            "description": "Skill certified successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Python 3.11",
                        "status": "certified",
                        "certification_date": "2026-01-16T10:35:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Skill not found",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://waooaw.com/errors/not-found",
                        "title": "Entity Not Found",
                        "status": 404,
                        "detail": "Skill with ID 550e8400-e29b-41d4-a716-446655440000 not found"
                    }
                }
            }
        }
    }
)
async def certify_skill(
    skill_id: UUID,
    certification_data: dict,
    db: Session = Depends(get_db)
):
    """
    Trigger Genesis certification workflow for Skill.
    
    This starts a Temporal workflow for multi-gate approval.
    """
    try:
        service = SkillService(db)
        skill = await service.certify_skill(skill_id, certification_data)
        return skill
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Certification failed: {str(e)}")


# =====================
# JOB ROLE ENDPOINTS
# =====================

@router.post("/job-roles", response_model=JobRoleResponse, status_code=201)
async def create_job_role(
    role_data: JobRoleCreate,
    db: Session = Depends(get_db)
):
    """
    Create new Job Role with skill requirements.
    
    - Validates required skills exist
    - Validates constitutional alignment
    - Returns JobRole entity
    """
    try:
        service = JobRoleService(db)
        job_role = await service.create_job_role(role_data)
        return job_role
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/job-roles", response_model=List[JobRoleResponse])
async def list_job_roles(
    seniority_level: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all job roles with optional filtering.
    
    - Filter by seniority (junior/mid/senior)
    - Pagination support
    """
    service = JobRoleService(db)
    roles = await service.list_job_roles(seniority_level=seniority_level, limit=limit, offset=offset)
    return roles


@router.get("/job-roles/{role_id}", response_model=JobRoleResponse)
async def get_job_role(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve Job Role by ID.
    """
    service = JobRoleService(db)
    role = await service.get_job_role_by_id(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail=f"Job Role {role_id} not found")
    
    return role
