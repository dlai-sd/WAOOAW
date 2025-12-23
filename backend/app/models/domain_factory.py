"""
Domain Factory Models - Agent Creation Factory Data Models

Implements the modular architecture:
- Components: Technical infrastructure (LLMs, APIs, integrations)
- Skills: Modular capabilities that use components
- Roles: Complete AI agents that bundle skills
- Teams: Bundled agent workforces with discount pricing
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Domain(BaseModel):
    """Industry domain (e.g., Digital Marketing, Healthcare, Sales)"""
    
    id: str = Field(..., description="Unique domain identifier (slug)")
    name: str = Field(..., description="Human-readable domain name")
    description: str = Field(..., description="Domain description")
    version: str = Field(default="1.0.0", description="Domain specification version")
    industries_served: List[str] = Field(
        default_factory=list,
        description="Target industries/customer types"
    )
    regulatory_context: Optional[str] = Field(
        None,
        description="Regulatory requirements (HIPAA, GDPR, etc.)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    maintained_by: str = Field(
        default="Domain Specification Manager Agent",
        description="Who maintains this domain"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "digital-marketing",
                "name": "Digital Marketing",
                "description": "Complete AI agent workforce for digital marketing operations",
                "version": "1.0.0",
                "industries_served": ["Technology", "Healthcare", "E-commerce"],
                "regulatory_context": "GDPR, CAN-SPAM, FTC guidelines"
            }
        }


class Component(BaseModel):
    """Technical infrastructure (LLM, API, integration)"""
    
    id: str = Field(..., description="Unique component identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Component name")
    type: str = Field(
        ...,
        description="Type: LLM, API, Data Integration, Tool"
    )
    provider: str = Field(..., description="Provider/source")
    purpose: str = Field(..., description="What this component does")
    cost_model: str = Field(..., description="Pricing model (token-based, API call, free)")
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of capabilities this component provides"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "gpt-4",
                "domain_id": "digital-marketing",
                "name": "GPT-4 (OpenAI)",
                "type": "LLM",
                "provider": "OpenAI",
                "purpose": "Advanced natural language understanding and generation",
                "cost_model": "Token-based ($0.03/1K input, $0.06/1K output)",
                "capabilities": ["Text generation", "Content writing", "Analysis"]
            }
        }


class Skill(BaseModel):
    """Modular capability that uses components"""
    
    id: str = Field(..., description="Unique skill identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="What this skill does")
    category: str = Field(..., description="Category (Content Creation, SEO, Analytics, etc.)")
    price_standalone: float = Field(..., description="Price when purchased individually (INR)")
    currency: str = Field(default="INR", description="Currency code")
    components_used: List[str] = Field(
        default_factory=list,
        description="Component IDs this skill uses"
    )
    capabilities: List[str] = Field(
        default_factory=list,
        description="What this skill can do"
    )
    deliverables: Dict[str, str] = Field(
        default_factory=dict,
        description="Deliverables for standard/premium tiers"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "blog-writing",
                "domain_id": "digital-marketing",
                "name": "Blog Writing",
                "description": "Create SEO-optimized blog posts (500-2000 words)",
                "category": "Content Creation",
                "price_standalone": 3000,
                "currency": "INR",
                "components_used": ["gpt-4", "wordpress-api"],
                "capabilities": ["Long-form content", "SEO optimization", "Meta descriptions"],
                "deliverables": {
                    "standard": "4 blog posts per month",
                    "premium": "8 blog posts per month"
                }
            }
        }


class Role(BaseModel):
    """Complete AI agent that bundles multiple skills"""
    
    id: str = Field(..., description="Unique role identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Agent role name")
    description: str = Field(..., description="What this agent does")
    specialty: Optional[str] = Field(
        None,
        description="Specialty/niche (e.g., Healthcare, E-commerce)"
    )
    skills_standard: List[str] = Field(
        default_factory=list,
        description="Skill IDs included in standard tier (4 skills)"
    )
    skills_premium: List[str] = Field(
        default_factory=list,
        description="Skill IDs included in premium tier (10 skills)"
    )
    price_standard: float = Field(..., description="Standard tier price (INR)")
    price_premium: Optional[float] = Field(
        None,
        description="Premium tier price (INR)"
    )
    currency: str = Field(default="INR", description="Currency code")
    billing_cycle: str = Field(default="monthly", description="Billing frequency")
    deliverables: Dict[str, Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="What agent delivers by tier and frequency"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent performance data (response time, quality rating, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "content-marketing-agent",
                "domain_id": "digital-marketing",
                "name": "Content Marketing Agent",
                "description": "Create and manage blog content, SEO optimization",
                "specialty": "Healthcare",
                "skills_standard": ["blog-writing", "seo-analysis", "content-calendar", "analytics"],
                "skills_premium": ["blog-writing", "seo-analysis", "content-calendar", "analytics", "competitor-analysis", "topic-ideation", "content-repurposing", "email-newsletter", "infographic-planning", "video-scripts"],
                "price_standard": 15000,
                "price_premium": 25000,
                "currency": "INR",
                "deliverables": {
                    "standard": {
                        "daily": ["1 blog post draft"],
                        "weekly": ["Content calendar", "SEO report"],
                        "monthly": ["Content strategy"]
                    }
                }
            }
        }


class Team(BaseModel):
    """Bundled agent workforce for an industry"""
    
    id: str = Field(..., description="Unique team identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team description")
    roles_included: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of role IDs with quantity, tier, priority"
    )
    individual_sum: float = Field(..., description="Sum of individual role prices")
    bundle_discount_percent: float = Field(..., description="Discount percentage for bundle")
    team_price: float = Field(..., description="Final team price after discount")
    savings: float = Field(..., description="Amount saved by buying as team")
    currency: str = Field(default="INR", description="Currency code")
    target_customers: List[str] = Field(
        default_factory=list,
        description="Who should buy this team"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "digital-marketing-workforce",
                "domain_id": "digital-marketing",
                "name": "Digital Marketing Workforce",
                "description": "Complete team of 7 AI agent employees",
                "roles_included": [
                    {"role_id": "content-marketing-agent", "quantity": 1, "tier": "standard", "priority": "Core"},
                    {"role_id": "seo-specialist", "quantity": 1, "tier": "standard", "priority": "Core"}
                ],
                "individual_sum": 94500,
                "bundle_discount_percent": 20,
                "team_price": 75000,
                "savings": 19500,
                "target_customers": ["SMBs", "Startups", "Agencies"]
            }
        }


# Relationship Models

class ComponentSkill(BaseModel):
    """Many-to-many: Skill uses Components"""
    component_id: str
    skill_id: str


class RoleSkill(BaseModel):
    """Many-to-many: Role bundles Skills"""
    role_id: str
    skill_id: str
    tier: str = Field(..., description="standard or premium")


class TeamRole(BaseModel):
    """Many-to-many: Team contains Roles"""
    team_id: str
    role_id: str
    quantity: int = Field(default=1, description="Number of this agent in team")
    tier: str = Field(..., description="standard or premium")
    priority: str = Field(..., description="Core, Optional, Advanced, or Meta")
