"""
Domain Factory Models - Agent Creation Factory Data Models

Implements the kitchen analogy:
- Ingredients: Basic building blocks
- Components: Reusable modules
- Recipes: Individual agent roles
- Cookbooks: Complete agent teams
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Domain(BaseModel):
    """Industry domain (e.g., Digital Marketing, Healthcare, Sales)"""
    
    id: str = Field(..., description="Unique domain identifier (slug)")
    name: str = Field(..., description="Human-readable domain name")
    description: str = Field(..., description="Domain description")
    expert_level: str = Field(
        default="PhD-equivalent domain knowledge",
        description="Level of expertise encoded"
    )
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
                "expert_level": "PhD-equivalent domain knowledge",
                "version": "1.0.0",
                "industries_served": ["Technology", "Healthcare", "E-commerce"],
                "regulatory_context": "GDPR, CAN-SPAM, FTC guidelines"
            }
        }


class Ingredient(BaseModel):
    """Basic building block (AI model, API, tool, library)"""
    
    id: str = Field(..., description="Unique ingredient identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Ingredient name")
    type: str = Field(
        ...,
        description="Type: AI Model, Integration, Software Library, Tool"
    )
    provider: str = Field(..., description="Provider/source of ingredient")
    purpose: str = Field(..., description="What this ingredient does")
    cost_model: str = Field(..., description="Pricing model (token-based, API call, fixed)")
    required_for: List[str] = Field(
        default_factory=list,
        description="Which recipes require this ingredient"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "nlp-engine",
                "domain_id": "digital-marketing",
                "name": "Natural Language Processing Engine",
                "type": "AI Model",
                "provider": "OpenAI GPT-4",
                "purpose": "Understanding and generating human-like text",
                "cost_model": "token-based",
                "required_for": ["content-marketing-specialist", "social-media-manager"]
            }
        }


class Component(BaseModel):
    """Reusable module shared across multiple agents"""
    
    id: str = Field(..., description="Unique component identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Component name")
    type: str = Field(
        ...,
        description="Type: Knowledge Module, Functional Module"
    )
    description: str = Field(..., description="What this component does")
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of capabilities this component provides"
    )
    contains: List[str] = Field(
        default_factory=list,
        description="Knowledge/skills contained in this component"
    )
    update_frequency: str = Field(
        default="Monthly",
        description="How often this component is updated"
    )
    used_by: str = Field(..., description="Which recipes use this component")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "digital-marketing-sme",
                "domain_id": "digital-marketing",
                "name": "Digital Marketing Subject Matter Expert",
                "type": "Knowledge Module",
                "description": "PhD-level expertise in digital marketing",
                "capabilities": [
                    "SEO best practices",
                    "Content marketing strategies",
                    "Social media expertise"
                ],
                "update_frequency": "Monthly",
                "used_by": "ALL agents in Digital Marketing domain"
            }
        }


class Recipe(BaseModel):
    """Individual agent role definition (complete recipe)"""
    
    id: str = Field(..., description="Unique recipe identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Agent role name")
    role: str = Field(..., description="What this agent does")
    specialty: Optional[str] = Field(
        None,
        description="Specialty/niche (e.g., Healthcare, E-commerce)"
    )
    core_skills: List[str] = Field(
        default_factory=list,
        description="Key skills this agent has"
    )
    deliverables: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="What agent delivers (daily, weekly, monthly)"
    )
    subscription_limits: Dict[str, str] = Field(
        default_factory=dict,
        description="Limits per subscription tier"
    )
    base_price: float = Field(..., description="Base monthly price")
    currency: str = Field(default="INR", description="Currency code")
    billing_cycle: str = Field(default="monthly", description="Billing frequency")
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent performance data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "content-marketing-specialist",
                "domain_id": "digital-marketing",
                "name": "Content Marketing Specialist Agent",
                "role": "Create and manage blog content, SEO-optimized articles",
                "specialty": "Healthcare",
                "core_skills": [
                    "Blog post writing (800-2000 words)",
                    "SEO keyword optimization",
                    "Content calendar creation"
                ],
                "deliverables": {
                    "daily": ["1 blog post draft"],
                    "weekly": ["Content calendar"],
                    "monthly": ["SEO content strategy"]
                },
                "base_price": 12000,
                "currency": "INR"
            }
        }


class Cookbook(BaseModel):
    """Complete team of agents for an industry"""
    
    id: str = Field(..., description="Unique cookbook identifier")
    domain_id: str = Field(..., description="Parent domain")
    name: str = Field(..., description="Cookbook name")
    description: str = Field(..., description="Team description")
    team_structure: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of agents in this team with priorities"
    )
    individual_sum: float = Field(..., description="Sum of individual agent prices")
    bundle_discount: float = Field(..., description="Discount percentage for bundle")
    team_price: float = Field(..., description="Final team price after discount")
    savings: float = Field(..., description="Amount saved by buying as team")
    target_customers: List[str] = Field(
        default_factory=list,
        description="Who should buy this team"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "digital-marketing-workforce",
                "domain_id": "digital-marketing",
                "name": "Digital Marketing Agent Workforce",
                "description": "Complete team of 7 AI agent employees",
                "individual_sum": 84000,
                "bundle_discount": 20,
                "team_price": 67200,
                "savings": 16800,
                "target_customers": ["SMBs", "Startups", "Agencies"]
            }
        }


# Relationship Models

class ComponentIngredient(BaseModel):
    """Many-to-many relationship: Component uses Ingredients"""
    component_id: str
    ingredient_id: str


class RecipeIngredient(BaseModel):
    """Many-to-many relationship: Recipe requires Ingredients"""
    recipe_id: str
    ingredient_id: str


class RecipeComponent(BaseModel):
    """Many-to-many relationship: Recipe uses Components"""
    recipe_id: str
    component_id: str


class CookbookRecipe(BaseModel):
    """Many-to-many relationship: Cookbook contains Recipes"""
    cookbook_id: str
    recipe_id: str
    quantity: int = Field(default=1, description="Number of this agent in team")
    priority: str = Field(
        ...,
        description="Core, Optional, Advanced, or Meta"
    )
