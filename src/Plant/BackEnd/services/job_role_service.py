"""
Job Role service - team composition + skill requirements
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import hashlib
import json

from models.job_role import JobRole
from models.schemas import JobRoleCreate, JobRoleResponse
from models.skill import Skill
from validators.constitutional_validator import validate_constitutional_alignment
from validators.entity_validator import validate_entity_uniqueness
from core.exceptions import ConstitutionalAlignmentError, DuplicateEntityError, ValidationError


class JobRoleService:
    """Service for managing Job Roles with skill requirements."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_job_role(self, role_data: JobRoleCreate) -> JobRole:
        """
        Create new Job Role with skill validation.
        
        Args:
            role_data: JobRoleCreate schema
        
        Returns:
            Created JobRole entity
        
        Raises:
            DuplicateEntityError: If role name already exists
            ValidationError: If required_skills are invalid
            ConstitutionalAlignmentError: If L0/L1 checks fail
        """
        # Check uniqueness
        existing = await validate_entity_uniqueness(
            self.db, JobRole, "name", role_data.name
        )
        if existing:
            raise DuplicateEntityError(f"Job Role '{role_data.name}' already exists")
        
        # Validate required skills exist
        if not role_data.required_skills:
            raise ValidationError("Job Role must have at least one required skill")
        
        skills = self.db.query(Skill).filter(
            Skill.id.in_(role_data.required_skills)
        ).all()
        
        if len(skills) != len(role_data.required_skills):
            raise ValidationError("One or more required skills do not exist")
        
        # Calculate version hash
        version_data = {
            "name": role_data.name,
            "required_skills": [str(s) for s in role_data.required_skills],
            "seniority_level": role_data.seniority_level,
        }
        version_hash = hashlib.sha256(
            json.dumps(version_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Create entity
        job_role = JobRole(
            name=role_data.name,
            description=role_data.description,
            required_skills=role_data.required_skills,
            seniority_level=role_data.seniority_level,
            entity_type="JobRole",
            governance_agent_id="genesis",
            version_hash=version_hash,
            hash_chain_sha256=[version_hash],
            amendment_history=[{"data": version_data, "timestamp": "now"}],
        )
        
        # Validate constitutional alignment
        validation_result = validate_constitutional_alignment(job_role)
        if not validation_result["compliant"]:
            raise ConstitutionalAlignmentError(
                f"Job Role failed L0/L1 checks: {validation_result['violations']}"
            )
        
        # Persist to database
        self.db.add(job_role)
        self.db.commit()
        self.db.refresh(job_role)
        
        return job_role
    
    async def get_job_role_by_id(self, role_id: UUID) -> Optional[JobRole]:
        """
        Retrieve Job Role by ID.
        
        Args:
            role_id: JobRole UUID
        
        Returns:
            JobRole entity or None
        """
        return self.db.query(JobRole).filter(JobRole.id == role_id).first()
    
    async def list_job_roles(
        self,
        seniority_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JobRole]:
        """
        List job roles with optional filtering.
        
        Args:
            seniority_level: Filter by seniority (junior/mid/senior)
            limit: Max results (default 100)
            offset: Pagination offset
        
        Returns:
            List of JobRole entities
        """
        query = self.db.query(JobRole).filter(JobRole.status == "active")
        
        if seniority_level:
            query = query.filter(JobRole.seniority_level == seniority_level)
        
        return query.limit(limit).offset(offset).all()
