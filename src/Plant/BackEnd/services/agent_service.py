"""
Agent service - birth, industry locking, constitutional enforcement
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import hashlib
import json

from models.agent import Agent
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team
from models.industry import Industry
from models.schemas import AgentCreate, AgentResponse
from validators.constitutional_validator import validate_constitutional_alignment
from validators.entity_validator import validate_entity_uniqueness
from core.exceptions import ConstitutionalAlignmentError, ValidationError


class AgentService:
    """Service for managing Agents with birth + industry locking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """
        Create new Agent (birth) with skill + role + industry locking.
        
        Args:
            agent_data: AgentCreate schema
        
        Returns:
            Created Agent entity
        
        Raises:
            ValidationError: If skill/role/industry invalid
            ConstitutionalAlignmentError: If L0/L1 checks fail
        """
        # Validate skill exists
        skill = self.db.query(Skill).filter(Skill.id == agent_data.skill_id).first()
        if not skill:
            raise ValidationError(f"Skill {agent_data.skill_id} not found")
        
        # Validate job role exists
        job_role = self.db.query(JobRole).filter(JobRole.id == agent_data.job_role_id).first()
        if not job_role:
            raise ValidationError(f"Job Role {agent_data.job_role_id} not found")
        
        # Validate industry exists
        industry = self.db.query(Industry).filter(Industry.id == agent_data.industry_id).first()
        if not industry:
            raise ValidationError(f"Industry {agent_data.industry_id} not found")
        
        # Calculate version hash
        version_data = {
            "name": agent_data.name,
            "skill_id": str(agent_data.skill_id),
            "job_role_id": str(agent_data.job_role_id),
            "industry_id": str(agent_data.industry_id),
        }
        version_hash = hashlib.sha256(
            json.dumps(version_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Create entity
        agent = Agent(
            name=agent_data.name,
            skill_id=agent_data.skill_id,
            job_role_id=agent_data.job_role_id,
            industry_id=agent_data.industry_id,
            entity_type="Agent",
            governance_agent_id="genesis",
            version_hash=version_hash,
            hash_chain_sha256=[version_hash],
            amendment_history=[{"data": version_data, "timestamp": "now"}],
        )
        
        # Validate constitutional alignment
        validation_result = validate_constitutional_alignment(agent)
        if not validation_result["compliant"]:
            raise ConstitutionalAlignmentError(
                f"Agent failed L0/L1 checks: {validation_result['violations']}"
            )
        
        # Persist to database
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    async def get_agent_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """
        Retrieve Agent by ID.
        
        Args:
            agent_id: Agent UUID
        
        Returns:
            Agent entity or None
        """
        return self.db.query(Agent).filter(Agent.id == agent_id).first()
    
    async def list_agents(
        self,
        industry_id: Optional[UUID] = None,
        job_role_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Agent]:
        """
        List agents with optional filtering.
        
        Args:
            industry_id: Filter by industry
            job_role_id: Filter by job role
            limit: Max results (default 100)
            offset: Pagination offset
        
        Returns:
            List of Agent entities
        """
        query = self.db.query(Agent).filter(Agent.status == "active")
        
        if industry_id:
            query = query.filter(Agent.industry_id == industry_id)
        
        if job_role_id:
            query = query.filter(Agent.job_role_id == job_role_id)
        
        return query.limit(limit).offset(offset).all()
    
    async def assign_agent_to_team(self, agent_id: UUID, team_id: UUID) -> Agent:
        """
        Assign Agent to Team.
        
        Args:
            agent_id: Agent UUID
            team_id: Team UUID
        
        Returns:
            Updated Agent
        
        Raises:
            ValidationError: If agent or team not found
        """
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            raise ValidationError(f"Agent {agent_id} not found")
        
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValidationError(f"Team {team_id} not found")
        
        # Update agent's team
        agent.team_id = team_id
        
        # Update team's agent list
        if team.agents is None:
            team.agents = []
        if agent_id not in team.agents:
            team.agents.append(agent_id)
        
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
