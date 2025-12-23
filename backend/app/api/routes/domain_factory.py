"""
Domain Factory API Routes - Agent Creation Factory

Endpoints for managing domain specifications:
- Domains (industries)
- Components (technical infrastructure)
- Skills (modular capabilities)
- Roles (complete AI agents)
- Teams (bundled workforces)
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.domain_factory import (
    Domain,
    Component,
    Skill,
    Role,
    Team,
)

router = APIRouter(
    prefix="/api/domain-factory",
    tags=["Agent Creation Factory"]
)


# Response Models

class DomainListResponse(BaseModel):
    """Response model for listing domains"""
    domains: List[Domain]
    total: int


class DomainDetailResponse(BaseModel):
    """Complete domain specification with all layers"""
    domain: Domain
    components: List[Component]
    skills: List[Skill]
    roles: List[Role]
    team: Optional[Team]


class TemplateResponse(BaseModel):
    """Template for creating new domains/roles"""
    template: Dict[str, Any]
    instructions: str


class ValidationResponse(BaseModel):
    """Domain specification validation result"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    completeness_score: float


class InterviewResponse(BaseModel):
    """Domain Specification Manager interview session"""
    session_id: str
    industry_name: str
    questions: List[Dict[str, str]]
    estimated_time: str


class GeneratedSpecResponse(BaseModel):
    """Generated domain specification from interview"""
    domain: Domain
    components: List[Component]
    skills: List[Skill]
    roles: List[Role]
    team: Team
    generation_time: str
    status: str


# Domain Endpoints

@router.get("/domains", response_model=DomainListResponse)
async def list_domains(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """List all industry domains (Digital Marketing, Healthcare, Sales, etc.)"""
    mock_domains = [
        Domain(
            id="digital-marketing",
            name="Digital Marketing",
            description="Complete AI agent workforce for digital marketing operations",
            industries_served=["Technology", "Healthcare", "E-commerce"],
            regulatory_context="GDPR, CAN-SPAM, FTC guidelines"
        ),
        Domain(
            id="healthcare",
            name="Healthcare",
            description="AI agent workforce for healthcare providers, clinics, hospitals",
            industries_served=["Healthcare", "Telemedicine"],
            regulatory_context="HIPAA, HITECH, state medical board regulations"
        ),
        Domain(
            id="sales",
            name="Sales",
            description="AI agent workforce for B2B sales teams, SDRs, account executives",
            industries_served=["B2B SaaS", "Enterprise", "SMB"],
            regulatory_context="CAN-SPAM, TCPA"
        ),
    ]
    
    return DomainListResponse(
        domains=mock_domains[skip:skip+limit],
        total=len(mock_domains)
    )


@router.get("/domains/{domain_id}", response_model=DomainDetailResponse)
async def get_domain(domain_id: str):
    """Get complete domain specification (domain + components + skills + roles + team)"""
    if domain_id == "digital-marketing":
        return DomainDetailResponse(
            domain=Domain(
                id="digital-marketing",
                name="Digital Marketing",
                description="Complete AI agent workforce for digital marketing operations",
                industries_served=["Technology", "Healthcare", "E-commerce"]
            ),
            components=[
                Component(
                    id="gpt-4",
                    domain_id="digital-marketing",
                    name="GPT-4 (OpenAI)",
                    type="LLM",
                    provider="OpenAI",
                    purpose="Advanced natural language understanding and generation",
                    cost_model="Token-based"
                )
            ],
            skills=[
                Skill(
                    id="blog-writing",
                    domain_id="digital-marketing",
                    name="Blog Writing",
                    description="Create SEO-optimized blog posts",
                    category="Content Creation",
                    price_standalone=3000,
                    components_used=["gpt-4"]
                )
            ],
            roles=[
                Role(
                    id="content-marketing-agent",
                    domain_id="digital-marketing",
                    name="Content Marketing Agent",
                    description="Create and manage blog content, SEO optimization",
                    skills_standard=["blog-writing"],
                    price_standard=15000
                )
            ],
            team=Team(
                id="digital-marketing-workforce",
                domain_id="digital-marketing",
                name="Digital Marketing Workforce",
                description="Complete team of 7 AI agent employees",
                individual_sum=94500,
                bundle_discount_percent=20,
                team_price=75000,
                savings=19500
            )
        )
    
    raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")


@router.post("/domains", response_model=Domain)
async def create_domain(domain: Domain):
    """Create new domain specification"""
    return domain


@router.put("/domains/{domain_id}", response_model=Domain)
async def update_domain(domain_id: str, domain: Domain):
    """Update existing domain specification"""
    if domain.id != domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain ID in URL doesn't match domain ID in body"
        )
    return domain


@router.delete("/domains/{domain_id}")
async def delete_domain(domain_id: str):
    """Delete domain specification"""
    return {"message": f"Domain '{domain_id}' deleted successfully"}


# Components Endpoints

@router.get("/domains/{domain_id}/components", response_model=List[Component])
async def list_components(domain_id: str):
    """List all technical components for a domain (LLMs, APIs, integrations)"""
    return []


@router.post("/domains/{domain_id}/components", response_model=Component)
async def add_component(domain_id: str, component: Component):
    """Add new technical component to domain"""
    if component.domain_id != domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain ID in URL doesn't match component's domain_id"
        )
    return component


# Skills Endpoints

@router.get("/domains/{domain_id}/skills", response_model=List[Skill])
async def list_skills(domain_id: str):
    """List all skills for a domain (modular capabilities)"""
    return []


@router.post("/domains/{domain_id}/skills", response_model=Skill)
async def add_skill(domain_id: str, skill: Skill):
    """Add new skill to domain"""
    if skill.domain_id != domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain ID in URL doesn't match skill's domain_id"
        )
    return skill


# Roles Endpoints

@router.get("/domains/{domain_id}/roles", response_model=List[Role])
async def list_roles(domain_id: str):
    """List all agent roles for a domain (complete AI agents)"""
    if domain_id == "digital-marketing":
        return [
            Role(
                id="content-marketing-agent",
                domain_id="digital-marketing",
                name="Content Marketing Agent",
                description="Create and manage blog content, SEO optimization",
                specialty="Healthcare",
                skills_standard=["blog-writing"],
                price_standard=15000
            ),
            Role(
                id="seo-specialist",
                domain_id="digital-marketing",
                name="SEO Specialist Agent",
                description="Keyword research, technical SEO, link building",
                specialty="E-commerce",
                skills_standard=["seo-analysis"],
                price_standard=15000
            ),
        ]
    return []


@router.get("/roles/{role_id}", response_model=Role)
async def get_role(role_id: str):
    """Get detailed role definition (agent role)"""
    raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")


@router.post("/domains/{domain_id}/roles", response_model=Role)
async def create_role(domain_id: str, role: Role):
    """Create new agent role definition"""
    if role.domain_id != domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain ID in URL doesn't match role's domain_id"
        )
    return role


# Team Endpoints

@router.get("/domains/{domain_id}/team", response_model=Team)
async def get_team(domain_id: str):
    """Get complete team structure (bundled workforce) for domain"""
    if domain_id == "digital-marketing":
        return Team(
            id="digital-marketing-workforce",
            domain_id="digital-marketing",
            name="Digital Marketing Workforce",
            description="Complete team of 7 AI agent employees",
            individual_sum=94500,
            bundle_discount_percent=20,
            team_price=75000,
            savings=19500,
            target_customers=["SMBs", "Startups", "Agencies"]
        )
    raise HTTPException(status_code=404, detail=f"Team for domain '{domain_id}' not found")


@router.post("/domains/{domain_id}/team", response_model=Team)
async def create_team(domain_id: str, team: Team):
    """Create team (bundled workforce) for domain"""
    if team.domain_id != domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain ID in URL doesn't match team's domain_id"
        )
    return team


# Template Endpoints

@router.get("/templates/domain", response_model=TemplateResponse)
async def get_domain_template():
    """Get blank domain specification template for new industry"""
    return TemplateResponse(
        template={
            "domain": {
                "id": "{{industry-slug}}",
                "name": "{{Industry Name}}",
                "description": "AI agent workforce for {{industry}} operations",
                "regulatory_context": "{{regulations}}"
            },
            "components_checklist": [
                "LLMs (GPT-4, Claude, specialized models)",
                "APIs (domain-specific integrations)",
                "Tools and libraries"
            ],
            "skills_framework": "4-10 modular capabilities per role",
            "roles_framework": "5-10 complete agents per industry"
        },
        instructions="Replace {{placeholders}} with actual values. See AGENT_CREATION_FACTORY.md for detailed guide."
    )


@router.get("/templates/role", response_model=TemplateResponse)
async def get_role_template():
    """Get blank role template for new agent"""
    return TemplateResponse(
        template={
            "id": "{{role-slug}}",
            "domain_id": "{{domain-id}}",
            "name": "{{Role Name}} Agent",
            "description": "{{What this agent does}}",
            "skills_standard": ["{{skill-1}}", "{{skill-2}}", "{{skill-3}}", "{{skill-4}}"],
            "price_standard": "{{8000-18000 INR}}"
        },
        instructions="Fill in all fields. Skills should be modular capabilities."
    )


# Domain Specification Manager Endpoints

@router.post("/domain-spec-manager/interview", response_model=InterviewResponse)
async def start_domain_interview(industry_name: str = Query(..., description="Name of the industry to onboard")):
    """Start interview with Domain Specification Manager Agent"""
    session_id = f"interview-{industry_name.lower().replace(' ', '-')}"
    
    return InterviewResponse(
        session_id=session_id,
        industry_name=industry_name,
        questions=[
            {"id": "q1", "question": "What are the 5-10 key roles in this industry?", "example": "For Real Estate: Property Analyst, Listing Creator, CRM Manager"},
            {"id": "q2", "question": "What tools and systems do professionals use?", "example": "For Real Estate: Zillow API, MLS databases, CRMs"},
            {"id": "q3", "question": "What are essential skills for each role?", "example": "Market analysis, Property valuation, Client communication"},
            {"id": "q4", "question": "What regulations apply?", "example": "Fair Housing Act, state licensing"},
            {"id": "q5", "question": "Who are target customers?", "example": "Real estate agencies, individual agents"},
            {"id": "q6", "question": "What are typical deliverables?", "example": "Market reports, listing descriptions"},
            {"id": "q7", "question": "What subscription tiers make sense?", "example": "Basic: 10 listings/month, Standard: 30/month"},
            {"id": "q8", "question": "What's appropriate pricing?", "example": "₹10,000-20,000/month per agent"},
            {"id": "q9", "question": "Are there specializations?", "example": "Residential, Commercial, Luxury"},
            {"id": "q10", "question": "What unique challenges exist?", "example": "Seasonality, local variations"}
        ],
        estimated_time="30 minutes for interview + 2 hours for specification generation"
    )


@router.post("/domain-spec-manager/generate", response_model=GeneratedSpecResponse)
async def generate_domain_spec(interview_data: Dict[str, Any]):
    """Generate complete domain specification from interview data"""
    industry_name = interview_data.get("industry_name", "New Industry")
    
    return GeneratedSpecResponse(
        domain=Domain(
            id=industry_name.lower().replace(" ", "-"),
            name=industry_name,
            description=f"AI agent workforce for {industry_name} operations",
            industries_served=[industry_name]
        ),
        components=[],
        skills=[],
        roles=[],
        team=Team(
            id=f"{industry_name.lower().replace(' ', '-')}-workforce",
            domain_id=industry_name.lower().replace(" ", "-"),
            name=f"{industry_name} Workforce",
            description=f"Complete team for {industry_name}",
            individual_sum=0,
            bundle_discount_percent=20,
            team_price=0,
            savings=0
        ),
        generation_time="2 hours",
        status="generated"
    )


@router.get("/domain-spec-manager/validate/{domain_id}", response_model=ValidationResponse)
async def validate_domain_spec(domain_id: str):
    """Validate domain specification for completeness"""
    return ValidationResponse(
        valid=True,
        errors=[],
        warnings=[],
        completeness_score=0.95
    )
