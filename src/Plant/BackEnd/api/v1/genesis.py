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

@router.post("/skills", response_model=SkillResponse, status_code=201)
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


@router.post("/skills/{skill_id}/certify", response_model=SkillResponse)
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
