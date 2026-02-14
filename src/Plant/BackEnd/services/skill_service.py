"""
Skill service - Genesis certification + constitutional alignment
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import json
import re

from models.skill import Skill
from models.schemas import SkillCreate, SkillResponse
from validators.constitutional_validator import validate_constitutional_alignment
from validators.entity_validator import validate_entity_uniqueness
from core.exceptions import ConstitutionalAlignmentError, DuplicateEntityError


def _derive_skill_key(name: str) -> str:
    normalized = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return (slug or "skill")[:255]


class SkillService:
    """Service for managing Skills with constitutional governance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_skill(self, skill_data: SkillCreate) -> Skill:
        """
        Create new Skill with L0/L1 validation.
        
        Args:
            skill_data: SkillCreate schema
        
        Returns:
            Created Skill entity
        
        Raises:
            DuplicateEntityError: If skill name already exists
            ConstitutionalAlignmentError: If L0/L1 checks fail
        """
        # Check uniqueness
        existing = await validate_entity_uniqueness(
            self.db, Skill, "name", skill_data.name
        )
        if existing:
            raise DuplicateEntityError(f"Skill '{skill_data.name}' already exists")

        skill_key = (
            skill_data.skill_key.strip()
            if getattr(skill_data, "skill_key", None) and skill_data.skill_key.strip()
            else _derive_skill_key(skill_data.name)
        )

        existing_key = await validate_entity_uniqueness(self.db, Skill, "external_id", skill_key)
        if existing_key:
            raise DuplicateEntityError(f"Skill key '{skill_key}' already exists")
        
        # Calculate version hash
        version_data = {
            "skill_key": skill_key,
            "name": skill_data.name,
            "description": skill_data.description,
            "category": skill_data.category,
        }
        version_hash = hashlib.sha256(
            json.dumps(version_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Create entity
        skill = Skill(
            external_id=skill_key,
            name=skill_data.name,
            description=skill_data.description,
            category=skill_data.category,
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash=version_hash,
            hash_chain_sha256=[version_hash],
            amendment_history=[{"data": version_data, "timestamp": "now"}],
        )
        
        # Validate constitutional alignment
        validation_result = validate_constitutional_alignment(skill)
        if not validation_result["compliant"]:
            raise ConstitutionalAlignmentError(
                f"Skill failed L0/L1 checks: {validation_result['violations']}"
            )
        
        # Persist to database
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        
        return skill
    
    async def get_skill_by_id(self, skill_id: UUID) -> Optional[Skill]:
        """
        Retrieve Skill by ID.
        
        Args:
            skill_id: Skill UUID
        
        Returns:
            Skill entity or None
        """
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def list_skills(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Skill]:
        """
        List skills with optional filtering.
        
        Args:
            category: Filter by category (technical/soft_skill/domain_expertise)
            limit: Max results (default 100)
            offset: Pagination offset
        
        Returns:
            List of Skill entities
        """
        stmt = select(Skill).where(Skill.status == "active")
        
        if category:
            stmt = stmt.where(Skill.category == category)
        
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def certify_skill(self, skill_id: UUID, certification_data: dict) -> Skill:
        """
        Certify Skill via Genesis certification workflow.
        
        This triggers a Temporal workflow for multi-gate approval.
        
        Args:
            skill_id: Skill UUID
            certification_data: Certification metadata
        
        Returns:
            Updated Skill with genesis_certification set
        """
        skill = await self.get_skill_by_id(skill_id)
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")
        
        # TODO: Trigger genesis_certification_workflow via Temporal
        # workflow_id = await temporal_client.start_workflow(
        #     "genesis_certification_workflow",
        #     args=[skill_id, certification_data]
        # )
        
        # For now, directly set certification
        skill.custom_attributes["genesis_certification"] = {
            "certified": True,
            "timestamp": "now",
            **certification_data,
        }
        
        await self.db.commit()
        await self.db.refresh(skill)
        
        return skill
