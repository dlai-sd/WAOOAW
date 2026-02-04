"""Agent Management API routes.

PP admin portal routes for agent CRUD operations via Plant API.

These handlers must forward the incoming Authorization header to the Plant
Gateway. Otherwise the Plant Gateway will treat calls as unauthenticated.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from api.deps import get_authorization_header
from api.security import require_admin
from core.config import Settings, get_settings
from clients.plant_client import (
    PlantAPIClient,
    get_plant_client,
    SkillCreate,
    JobRoleCreate,
    AgentCreate,
    AgentResponse,
    PlantAPIError,
    ConstitutionalAlignmentError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)


router = APIRouter(prefix="/agents", tags=["agents"])


DEFAULT_SKILLS = [
    ("Content Marketing", "Create content strategies and campaigns", "domain_expertise"),
    ("SEO", "Improve search visibility and technical SEO", "technical"),
    ("Social Media", "Plan and execute social growth", "domain_expertise"),
    ("Email Marketing", "Lifecycle and newsletter campaigns", "domain_expertise"),
    ("PPC Advertising", "Paid acquisition and conversion optimization", "domain_expertise"),
    ("Math Tutoring", "Teach math concepts and exam prep", "domain_expertise"),
    ("Science Tutoring", "Teach science concepts and exam prep", "domain_expertise"),
    ("English Tutoring", "Teach English language skills", "domain_expertise"),
    ("Lead Generation", "Prospecting, outbound, and lead sourcing", "domain_expertise"),
    ("CRM Management", "Pipeline hygiene and CRM operations", "domain_expertise"),
]


DEFAULT_JOB_ROLES = [
    (
        "Content Marketing Specialist",
        "Creates high-quality content aligned to growth goals",
        ["Content Marketing", "SEO"],
        "mid",
    ),
    (
        "Social Media Manager",
        "Runs social strategy, posts, and community management",
        ["Social Media", "Content Marketing"],
        "mid",
    ),
    (
        "SEO Specialist",
        "On-page + technical SEO for sustained traffic",
        ["SEO"],
        "mid",
    ),
    (
        "Email Marketing Specialist",
        "Lifecycle email, onboarding, and retention programs",
        ["Email Marketing", "Content Marketing"],
        "mid",
    ),
    (
        "PPC Specialist",
        "Paid acquisition across search/social channels",
        ["PPC Advertising"],
        "mid",
    ),
    (
        "Math Tutor",
        "Math tutoring for test prep and coursework",
        ["Math Tutoring"],
        "mid",
    ),
    (
        "Science Tutor",
        "Science tutoring for test prep and coursework",
        ["Science Tutoring"],
        "mid",
    ),
    (
        "English Tutor",
        "English language tutoring and writing support",
        ["English Tutoring"],
        "mid",
    ),
    (
        "Sales Development Representative",
        "Outbound prospecting, qualification, and meeting setting",
        ["Lead Generation", "CRM Management"],
        "mid",
    ),
]


DEFAULT_AGENTS = [
    ("Content Marketing", "Asha — Content Marketing (Healthcare)", "Writes content plans and posts", "marketing"),
    ("Social Media Manager", "Rohan — Social Media (B2B)", "Plans posts and engagement", "marketing"),
    ("SEO Specialist", "Meera — SEO (E-commerce)", "SEO audits and content briefs", "marketing"),
    ("Email Marketing Specialist", "Kabir — Email Marketing", "Lifecycle emails and newsletters", "marketing"),
    ("PPC Specialist", "Isha — PPC Advertising", "Campaign setup and optimization", "marketing"),
    ("Math Tutor", "Neel — Math Tutor (JEE/NEET)", "Explains concepts and drills", "education"),
    ("Science Tutor", "Ananya — Science Tutor (CBSE)", "Science help and revision", "education"),
    ("English Tutor", "Zara — English Language", "Language + writing help", "education"),
    ("Sales Development Representative", "Vikram — SDR (B2B SaaS)", "Outbound and qualification", "sales"),
]


@router.post(
    "/seed-defaults",
    response_model=dict,
    summary="Seed baseline master data (dev-only)",
)
async def seed_defaults(
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    app_settings: Settings = Depends(get_settings),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Seed a small baseline dataset (skills, job roles, agents) via Plant APIs.

    This avoids direct DB migrations/SQL and keeps PP as the control surface.
    """
    if app_settings.is_prod_like or not app_settings.ENABLE_AGENT_SEEDING:
        raise HTTPException(status_code=404, detail="Not found")

    created = {"skills": 0, "job_roles": 0, "agents": 0}

    # Skills
    existing_skills = await plant_client.list_skills(limit=500, offset=0, auth_header=auth_header)
    skill_by_name = {s.name: s for s in existing_skills}
    for name, description, category in DEFAULT_SKILLS:
        if name in skill_by_name:
            continue
        try:
            s = await plant_client.create_skill(
                SkillCreate(name=name, description=description, category=category),
                auth_header=auth_header,
            )
            created["skills"] += 1
            skill_by_name[s.name] = s
            # Best-effort certify
            try:
                await plant_client.certify_skill(s.id, {}, auth_header=auth_header)
            except Exception:
                pass
        except DuplicateEntityError:
            pass

    # Job roles (need skill IDs)
    existing_roles = await plant_client.list_job_roles(limit=500, offset=0, auth_header=auth_header)
    role_by_name = {r.name: r for r in existing_roles}
    for name, description, required_skill_names, seniority in DEFAULT_JOB_ROLES:
        if name in role_by_name:
            continue
        required_skill_ids = [skill_by_name[n].id for n in required_skill_names if n in skill_by_name]
        if not required_skill_ids:
            raise HTTPException(status_code=409, detail=f"Missing required skills for job role: {name}")

        try:
            r = await plant_client.create_job_role(
                JobRoleCreate(
                    name=name,
                    description=description,
                    required_skills=required_skill_ids,
                    seniority_level=seniority,
                ),
                auth_header=auth_header,
            )
            created["job_roles"] += 1
            role_by_name[r.name] = r
            try:
                await plant_client.certify_job_role(r.id, {}, auth_header=auth_header)
            except Exception:
                pass
        except DuplicateEntityError:
            pass

    # Agents
    existing_agents = await plant_client.list_agents(limit=1000, offset=0, auth_header=auth_header)
    agent_names = {a.name for a in existing_agents if a.name}

    for job_role_name, agent_name, agent_description, industry in DEFAULT_AGENTS:
        if agent_name in agent_names:
            continue
        role = role_by_name.get(job_role_name)
        if not role:
            raise HTTPException(status_code=409, detail=f"Missing job role for agent: {agent_name}")

        try:
            await plant_client.create_agent(
                AgentCreate(
                    name=agent_name,
                    description=agent_description,
                    job_role_id=role.id,
                    industry=industry,
                    governance_agent_id="genesis",
                ),
                auth_header=auth_header,
            )
            created["agents"] += 1
        except DuplicateEntityError:
            pass

    return {
        "message": "Seed completed",
        "created": created,
        "note": "Run again safely; existing items are skipped when possible.",
    }


@router.post("", response_model=dict, status_code=201,
    summary="Create new agent entity",
    description="""
    Create a new AI agent in the Plant backend.
    
    **Workflow:**
    1. PP admin submits agent details (name, job role, industry)
    2. PP calls Plant API to create agent
    3. Agent created with initial "inactive" status
    4. Governor can activate agent after review
    
    **Constitutional Validation (Plant enforces):**
    - L0-01: governance_agent_id required
    - L0-02: Job role must be certified
    - L0-03: Agent name uniqueness within team
    - L0-05: Audit trail initialized
    
    **Returns:**
    - 201 Created: Agent entity with UUID
    - 404 Not Found: Referenced job role doesn't exist
    - 422 Unprocessable Entity: Validation error
    """)
async def create_agent(
    agent_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Create new agent via Plant API.
    
    Body:
    {
        "name": "Content Writer Agent #1",
        "description": "Creates marketing content",
        "job_role_id": "job-role-uuid",
        "industry": "marketing",
        "team_id": "team-uuid" (optional),
        "governance_agent_id": "genesis"
    }
    """
    try:
        # Convert dict to AgentCreate object
        agent_create = AgentCreate(
            name=agent_data["name"],
            description=agent_data["description"],
            job_role_id=agent_data["job_role_id"],
            industry=agent_data.get("industry", "general"),
            team_id=agent_data.get("team_id"),
            governance_agent_id=agent_data.get("governance_agent_id", "genesis")
        )
        
        # Call Plant API
        agent = await plant_client.create_agent(
            agent_create,
            auth_header=auth_header,
        )
        
        # TODO: Log to PP audit trail
        # await audit_service.log_action("agent.created", agent.id, current_user.id)
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "job_role_id": agent.job_role_id,
            "industry": agent.industry,
            "status": agent.status,
            "created_at": agent.created_at,
            "message": "Agent created successfully. Status: inactive. Governor review required for activation."
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("", response_model=List[dict],
    summary="List all agents with filters",
    description="""
    Retrieve list of agents from Plant.
    
    **Query Parameters:**
    - industry: Filter by industry (marketing/education/sales/healthcare/finance/general)
    - job_role_id: Filter by job role
    - status: Filter by status (active/inactive/suspended)
    - limit: Maximum results (default 100)
    - offset: Pagination offset (default 0)
    
    **Returns:**
    - 200 OK: Array of agent entities
    """)
async def list_agents(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    job_role_id: Optional[str] = Query(None, description="Filter by job role ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """List all agents with optional filtering."""
    try:
        agents = await plant_client.list_agents(
            industry=industry,
            job_role_id=job_role_id,
            status=status,
            limit=limit,
            offset=offset,
            auth_header=auth_header,
        )
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "job_role_id": agent.job_role_id,
                "industry": agent.industry,
                "industry_id": getattr(agent, "industry_id", None),
                "status": agent.status,
                "team_id": agent.team_id,
                "team_name": getattr(agent, "team_name", None),
                "created_at": agent.created_at
            }
            for agent in agents
        ]
    
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/{agent_id}", response_model=dict,
    summary="Get agent details by ID",
    description="Retrieve detailed information about a specific agent.")
async def get_agent(
    agent_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """Get agent by ID."""
    try:
        agent = await plant_client.get_agent(agent_id, auth_header=auth_header)
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "job_role_id": agent.job_role_id,
            "industry": agent.industry,
            "entity_type": agent.entity_type,
            "status": agent.status,
            "team_id": agent.team_id,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "l0_compliance_status": agent.l0_compliance_status
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.post("/{agent_id}/assign-team", response_model=dict,
    summary="Assign agent to team",
    description="""
    Assign an agent to a team.
    
    **Authorization (Future):**
    - Requires Governor or Team Lead role
    
    **Workflow:**
    1. PP admin selects agent and target team
    2. PP calls Plant API to update team assignment
    3. Plant validates team exists and capacity
    4. Agent team_id updated
    5. Assignment logged to audit trail
    
    **Returns:**
    - 200 OK: Agent assigned successfully
    - 404 Not Found: Agent or team doesn't exist
    - 422 Unprocessable Entity: Team capacity exceeded or other validation error
    """)
async def assign_agent_to_team(
    agent_id: str,
    assignment_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Assign agent to team.
    
    Body:
    {
        "team_id": "team-uuid"
    }
    """
    try:
        # TODO: Check current_user has Governor or Team Lead role (RBAC - future)
        # if not current_user.has_role(["governor", "team_lead"]):
        #     raise HTTPException(status_code=403, detail="Governor or Team Lead role required")
        
        team_id = assignment_data.get("team_id")
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id is required")
        
        # Call Plant API
        agent = await plant_client.assign_agent_to_team(
            agent_id,
            team_id,
            auth_header=auth_header,
        )
        
        # TODO: Log assignment event
        # await audit_service.log_action("agent.assigned_to_team", agent.id, current_user.id, {"team_id": team_id})
        
        return {
            "id": agent.id,
            "name": agent.name,
            "team_id": agent.team_id,
            "message": f"Agent assigned to team {team_id} successfully"
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.patch("/{agent_id}/status", response_model=dict,
    summary="Update agent status",
    description="""
    Update agent status (activate/deactivate/suspend).
    
    **Authorization (Future):**
    - Requires Governor role
    
    **Status Transitions:**
    - inactive → active (activation by Governor)
    - active → inactive (deactivation)
    - active → suspended (suspension due to policy violation)
    - suspended → active (reinstatement by Governor)
    
    **Returns:**
    - 200 OK: Agent status updated
    - 404 Not Found: Agent doesn't exist
    - 422 Unprocessable Entity: Invalid status transition
    """)
async def update_agent_status(
    agent_id: str,
    status_data: dict,
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Update agent status.
    
    Body:
    {
        "status": "active",
        "reason": "Governor approval received" (optional)
    }
    """
    try:
        # TODO: Check current_user has Governor role (RBAC - future)
        # if not current_user.has_role("governor"):
        #     raise HTTPException(status_code=403, detail="Governor role required")
        
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="status is required")
        
        if new_status not in ["active", "inactive", "suspended"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, inactive, or suspended")
        
        # NOTE: This endpoint doesn't exist in Plant yet - would need to add
        # For now, this is a placeholder for future implementation
        raise HTTPException(status_code=501, detail="Status update endpoint not yet implemented in Plant API")
        
        # Future implementation:
        # agent = await plant_client.update_agent_status(agent_id, new_status, status_data.get("reason"))
        # await audit_service.log_action("agent.status_updated", agent.id, current_user.id, {"new_status": new_status})
        # return {"id": agent.id, "name": agent.name, "status": agent.status, "message": "Agent status updated"}
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")
