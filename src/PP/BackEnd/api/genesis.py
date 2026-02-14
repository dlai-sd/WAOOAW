"""
Genesis API Routes - Skill and Job Role Certification
PP admin portal routes that proxy to Plant Genesis API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import (
    PlantAPIClient,
    get_plant_client,
    SkillCreate,
    SkillResponse,
    JobRoleCreate,
    JobRoleResponse,
    PlantAPIError,
    ConstitutionalAlignmentError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)


router = APIRouter(prefix="/genesis", tags=["genesis"], dependencies=[Depends(require_admin)])


# ========== SKILL ENDPOINTS ==========

@router.post("/skills", response_model=dict, status_code=201,
    summary="Create new skill (pending Genesis certification)",
    description="""
    Create a new skill entity that will be pending Genesis certification.
    
    **Workflow:**
    1. PP admin submits skill details
    2. PP calls Plant API to create skill
    3. Skill created with status="pending_certification"
    4. Genesis agent reviews and certifies skill
    
    **Constitutional Validation (Plant enforces):**
    - L0-01: governance_agent_id required
    - L0-02: Skill uniqueness (name + category)
    - L0-05: Audit trail initialized
    
    **Returns:**
    - 201 Created: Skill entity with UUID
    - 409 Conflict: Duplicate skill exists
    - 422 Unprocessable Entity: Validation error
    """)
async def create_skill(
    skill_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Create new skill via Plant API.
    
    Body:
    {
        "name": "Python 3.11",
        "description": "Modern Python programming",
        "category": "technical",
        "governance_agent_id": "genesis"
    }
    """
    try:
        # Convert dict to SkillCreate object
        skill_create = SkillCreate(
            name=skill_data["name"],
            description=skill_data["description"],
            category=skill_data["category"],
            governance_agent_id=skill_data.get("governance_agent_id", "genesis")
        )
        
        # Call Plant API
        skill = await plant_client.create_skill(skill_create, auth_header=auth_header)
        
        # TODO: Log to PP audit trail
        # await audit_service.log_action("skill.created", skill.id, current_user.id)
        
        return {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "status": skill.status,
            "created_at": skill.created_at,
            "message": "Skill created successfully. Pending Genesis certification."
        }
    
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/skills", response_model=List[dict],
    summary="List all skills with optional filtering",
    description="""
    Retrieve list of skills from Plant.
    
    **Query Parameters:**
    - category: Filter by category (technical/soft_skill/domain_expertise)
    - limit: Maximum results (default 100)
    - offset: Pagination offset (default 0)
    
    **Returns:**
    - 200 OK: Array of skill entities
    """)
async def list_skills(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """List all skills with optional filtering."""
    try:
        skills = await plant_client.list_skills(
            category=category,
            limit=limit,
            offset=offset,
            auth_header=auth_header,
        )
        
        return [
            {
                "id": skill.id,
                "skill_key": getattr(skill, "external_id", None),
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "status": skill.status,
                "created_at": skill.created_at
            }
            for skill in skills
        ]
    
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/skills/{skill_id}", response_model=dict,
    summary="Get skill details by ID",
    description="Retrieve detailed information about a specific skill.")
async def get_skill(
    skill_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """Get skill by ID."""
    try:
        skill = await plant_client.get_skill(skill_id, auth_header=auth_header)
        
        return {
            "id": skill.id,
            "skill_key": getattr(skill, "external_id", None),
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "entity_type": skill.entity_type,
            "status": skill.status,
            "created_at": skill.created_at,
            "updated_at": skill.updated_at,
            "l0_compliance_status": skill.l0_compliance_status
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.post("/skills/{skill_id}/certify", response_model=dict,
    summary="Certify skill via Genesis workflow",
    description="""
    Trigger Genesis certification for a pending skill.
    
    **Authorization (Future):**
    - Requires Genesis role or Governor permission
    
    **Workflow:**
    1. PP admin clicks "Certify" button
    2. PP calls Plant Genesis API
    3. Plant validates constitutional compliance
    4. Skill status updated to "certified"
    5. Certification event logged to audit trail
    
    **Returns:**
    - 200 OK: Skill certified successfully
    - 404 Not Found: Skill doesn't exist
    - 422 Unprocessable Entity: Certification requirements not met
    """)
async def certify_skill(
    skill_id: str,
    certification_data: dict = None,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Certify skill (Genesis role required in future).
    
    Body (optional):
    {
        "certification_notes": "Skill validated by Genesis Agent",
        "approval_gate": "technical_review"
    }
    """
    try:
        # TODO: Check current_user has Genesis role (RBAC - future)
        # if not current_user.has_role("genesis"):
        #     raise HTTPException(status_code=403, detail="Genesis role required")
        
        # Call Plant API
        skill = await plant_client.certify_skill(skill_id, certification_data or {}, auth_header=auth_header)
        
        # TODO: Log certification event
        # await audit_service.log_action("skill.certified", skill.id, current_user.id)
        
        return {
            "id": skill.id,
            "name": skill.name,
            "status": skill.status,
            "message": "Skill certified successfully"
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


# ========== JOB ROLE ENDPOINTS ==========

@router.post("/job-roles", response_model=dict, status_code=201,
    summary="Create new job role (pending Genesis certification)",
    description="""
    Create a new job role entity with required skills.
    
    **Constitutional Validation (Plant enforces):**
    - L0-01: governance_agent_id required
    - L0-02: Required skills must be certified
    - L0-05: Audit trail initialized
    
    **Returns:**
    - 201 Created: Job role entity with UUID
    - 404 Not Found: Referenced skill doesn't exist
    - 422 Unprocessable Entity: Validation error
    """)
async def create_job_role(
    job_role_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Create new job role via Plant API.
    
    Body:
    {
        "name": "Content Writer",
        "description": "Creates engaging content",
        "required_skills": ["skill-uuid-1", "skill-uuid-2"],
        "seniority_level": "mid",
        "governance_agent_id": "genesis"
    }
    """
    try:
        # Convert dict to JobRoleCreate object
        job_role_create = JobRoleCreate(
            name=job_role_data["name"],
            description=job_role_data["description"],
            required_skills=job_role_data["required_skills"],
            seniority_level=job_role_data.get("seniority_level", "mid"),
            governance_agent_id=job_role_data.get("governance_agent_id", "genesis")
        )
        
        # Call Plant API
        job_role = await plant_client.create_job_role(job_role_create, auth_header=auth_header)
        
        # TODO: Log to PP audit trail
        # await audit_service.log_action("job_role.created", job_role.id, current_user.id)
        
        return {
            "id": job_role.id,
            "name": job_role.name,
            "description": job_role.description,
            "required_skills": job_role.required_skills,
            "seniority_level": job_role.seniority_level,
            "status": job_role.status,
            "created_at": job_role.created_at,
            "message": "Job role created successfully. Pending Genesis certification."
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/job-roles", response_model=List[dict],
    summary="List all job roles",
    description="Retrieve list of job roles from Plant.")
async def list_job_roles(
    limit: int = 100,
    offset: int = 0,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """List all job roles with pagination."""
    try:
        job_roles = await plant_client.list_job_roles(limit=limit, offset=offset, auth_header=auth_header)
        
        return [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "required_skills": role.required_skills,
                "seniority_level": role.seniority_level,
                "status": role.status,
                "created_at": role.created_at
            }
            for role in job_roles
        ]
    
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/job-roles/{job_role_id}", response_model=dict,
    summary="Get job role details by ID")
async def get_job_role(
    job_role_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """Get job role by ID."""
    try:
        job_role = await plant_client.get_job_role(job_role_id, auth_header=auth_header)
        
        return {
            "id": job_role.id,
            "name": job_role.name,
            "description": job_role.description,
            "required_skills": job_role.required_skills,
            "seniority_level": job_role.seniority_level,
            "entity_type": job_role.entity_type,
            "status": job_role.status,
            "created_at": job_role.created_at
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.post("/job-roles/{job_role_id}/certify", response_model=dict,
    summary="Certify job role via Genesis workflow")
async def certify_job_role(
    job_role_id: str,
    certification_data: dict = None,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """Certify job role (Genesis role required in future)."""
    try:
        # TODO: Check current_user has Genesis role (RBAC - future)
        
        # Call Plant API
        job_role = await plant_client.certify_job_role(job_role_id, certification_data or {}, auth_header=auth_header)
        
        # TODO: Log certification event
        # await audit_service.log_action("job_role.certified", job_role.id, current_user.id)
        
        return {
            "id": job_role.id,
            "name": job_role.name,
            "status": job_role.status,
            "message": "Job role certified successfully"
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")
