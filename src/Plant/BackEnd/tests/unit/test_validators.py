"""
Unit tests for constitutional alignment validators and entity validators
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock

from models.base_entity import BaseEntity
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team
from models.agent import Agent
from models.industry import Industry
from validators.constitutional_validator import validate_constitutional_alignment
from validators.entity_validator import validate_entity_uniqueness


class TestL0Compliance:
    """Test L0 foundational governance checks."""
    
    def test_l0_01_governance_agent_id_present(self):
        """Test L0-01: governance_agent_id must be present."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(entity)
        
        assert result["checks"]["l0_01"] is True
    
    def test_l0_02_amendment_history_tracked(self):
        """Test L0-02: amendment_history must be tracked."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash123",
            amendment_history=[],
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(entity)
        
        assert result["checks"]["l0_02"] is True


class TestL1SkillValidation:
    """Test L1 Skill-specific rules."""
    
    def test_skill_validation_passes_for_valid_skill(self):
        """Test that valid Skill passes L1 checks."""
        skill = Skill(
            name="Python",
            description="Python programming",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(skill)
        
        assert result["compliant"] is True
        assert result["checks"]["l1_skill_validation"] is True
    
    def test_skill_validation_fails_without_name(self):
        """Test that Skill without name fails L1-SKILL-01."""
        skill = Skill(
            name="",
            description="Python programming",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(skill)
        
        assert result["compliant"] is False
        assert any("L1-SKILL-01" in v for v in result["violations"])


class TestEntityUniqueness:
    """Test entity uniqueness validation."""
    
    @pytest.mark.asyncio
    async def test_validate_entity_uniqueness_returns_true_when_no_duplicate(self):
        """Test uniqueness check returns None when no duplicate exists."""
        # Mock database session
        db_session = Mock()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        db_session.execute = AsyncMock(return_value=mock_result)
        
        result = await validate_entity_uniqueness(db_session, Skill, "name", "NewSkill")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_entity_uniqueness_returns_false_when_duplicate_exists(self):
        """Test uniqueness check returns entity when duplicate found."""
        # Mock database session with existing entity
        db_session = Mock()
        existing_skill = Mock()
        existing_skill.name = "ExistingSkill"
        existing_skill.status = "active"
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_skill
        db_session.execute = AsyncMock(return_value=mock_result)
        
        result = await validate_entity_uniqueness(db_session, Skill, "name", "ExistingSkill")
        
        assert result is not None
        assert result.name == "ExistingSkill"
    
    @pytest.mark.asyncio
    async def test_validate_entity_uniqueness_handles_unknown_entity_type(self):
        """Test uniqueness check works with any model."""
        db_session = Mock()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        db_session.execute = AsyncMock(return_value=mock_result)
        
        result = await validate_entity_uniqueness(db_session, Skill, "name", "test")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_entity_uniqueness_checks_all_entity_types(self):
        """Test uniqueness validation works for all entity types."""
        entity_models = [Skill, JobRole, Team, Agent, Industry]
        
        for Model in entity_models:
            db_session = Mock()
            mock_result = Mock()
            mock_result.scalars.return_value.first.return_value = None
            db_session.execute = AsyncMock(return_value=mock_result)
            
            result = await validate_entity_uniqueness(db_session, Model, "name", f"Test{Model.__name__}")
            
            assert result is None


class TestL1SkillValidationDetailed:
    """Test comprehensive L1-SKILL checks."""
    
    def test_skill_fails_without_description(self):
        """Test L1-SKILL-02: description required."""
        skill = Skill(
            name="Python",
            description="",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(skill)
        
        assert result["compliant"] is False
        assert any("L1-SKILL-02" in v for v in result["violations"])
    
    def test_skill_fails_with_invalid_category(self):
        """Test L1-SKILL-03: category must be valid."""
        skill = Skill(
            name="Python",
            description="Python programming",
            category="invalid_category",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(skill)
        
        assert result["compliant"] is False
        assert any("L1-SKILL-03" in v for v in result["violations"])
    
    def test_skill_passes_with_all_valid_categories(self):
        """Test that all valid categories pass."""
        valid_categories = ["technical", "soft_skill", "domain_expertise", "certification"]
        
        for category in valid_categories:
            skill = Skill(
                name="TestSkill",
                description="Test description",
                category=category,
                entity_type="Skill",
                governance_agent_id="genesis",
                version_hash="hash123",
                hash_chain_sha256=["hash123"],
            )
            
            result = validate_constitutional_alignment(skill)
            assert result["compliant"] is True, f"Category {category} should be valid"


class TestL1JobRoleValidation:
    """Test L1-JOBROLE checks."""
    
    def test_job_role_fails_without_required_skills(self):
        """Test L1-JOBROLE-01: required_skills cannot be empty."""
        job_role = JobRole(
            name="Software Engineer",
            required_skills=[],
            seniority_level="mid",
            entity_type="JobRole",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(job_role)
        
        assert result["compliant"] is False
        assert any("L1-JOBROLE-01" in v for v in result["violations"])
    
    def test_job_role_fails_with_invalid_seniority(self):
        """Test L1-JOBROLE-02: seniority must be valid."""
        job_role = JobRole(
            name="Software Engineer",
            required_skills=["Python"],
            seniority_level="invalid",
            entity_type="JobRole",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(job_role)
        
        assert result["compliant"] is False
        assert any("L1-JOBROLE-02" in v for v in result["violations"])
    
    def test_job_role_fails_without_name(self):
        """Test L1-JOBROLE-03: name required."""
        job_role = JobRole(
            name="",
            required_skills=["Python"],
            seniority_level="mid",
            entity_type="JobRole",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(job_role)
        
        assert result["compliant"] is False
        assert any("L1-JOBROLE-03" in v for v in result["violations"])
    
    def test_job_role_passes_with_all_valid_fields(self):
        """Test valid JobRole passes all checks."""
        for seniority in ["junior", "mid", "senior"]:
            job_role = JobRole(
                name="Engineer",
                required_skills=["Python", "JavaScript"],
                seniority_level=seniority,
                entity_type="JobRole",
                governance_agent_id="genesis",
                version_hash="hash123",
                hash_chain_sha256=["hash123"],
            )
            
            result = validate_constitutional_alignment(job_role)
            assert result["compliant"] is True


class TestL1TeamValidation:
    """Test L1-TEAM checks."""
    
    def test_team_fails_without_agents(self):
        """Test L1-TEAM-01: must have at least one agent."""
        team = Team(
            name="Dev Team",
            agents=[],
            job_role_id="role123",
            entity_type="Team",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(team)
        
        assert result["compliant"] is False
        assert any("L1-TEAM-01" in v for v in result["violations"])
    
    def test_team_fails_without_job_role_id(self):
        """Test L1-TEAM-02: job_role_id must be set."""
        team = Team(
            name="Dev Team",
            agents=["agent1"],
            job_role_id=None,
            entity_type="Team",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(team)
        
        assert result["compliant"] is False
        assert any("L1-TEAM-02" in v for v in result["violations"])
    
    def test_team_passes_with_valid_fields(self):
        """Test valid Team passes all checks."""
        team = Team(
            name="Dev Team",
            agents=["agent1", "agent2"],
            job_role_id="role123",
            entity_type="Team",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(team)
        assert result["compliant"] is True


class TestL1AgentValidation:
    """Test L1-AGENT checks."""
    
    def test_agent_fails_without_skill_id(self):
        """Test L1-AGENT-01: skill_id must be set."""
        agent = Agent(
            name="TestAgent",
            skill_id=None,
            job_role_id="role123",
            industry_id="ind123",
            entity_type="Agent",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(agent)
        
        assert result["compliant"] is False
        assert any("L1-AGENT-01" in v for v in result["violations"])
    
    def test_agent_fails_without_job_role_id(self):
        """Test L1-AGENT-02: job_role_id must be set."""
        agent = Agent(
            name="TestAgent",
            skill_id="skill123",
            job_role_id=None,
            industry_id="ind123",
            entity_type="Agent",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(agent)
        
        assert result["compliant"] is False
        assert any("L1-AGENT-02" in v for v in result["violations"])
    
    def test_agent_fails_without_industry_id(self):
        """Test L1-AGENT-03: industry_id must be set."""
        agent = Agent(
            name="TestAgent",
            skill_id="skill123",
            job_role_id="role123",
            industry_id=None,
            entity_type="Agent",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(agent)
        
        assert result["compliant"] is False
        assert any("L1-AGENT-03" in v for v in result["violations"])
    
    def test_agent_passes_with_all_required_ids(self):
        """Test valid Agent passes all checks."""
        agent = Agent(
            name="TestAgent",
            skill_id="skill123",
            job_role_id="role123",
            industry_id="ind123",
            entity_type="Agent",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(agent)
        assert result["compliant"] is True


class TestL1IndustryValidation:
    """Test L1-INDUSTRY checks."""
    
    def test_industry_fails_without_name(self):
        """Test L1-INDUSTRY-01: name required."""
        industry = Industry(
            name="",
            entity_type="Industry",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(industry)
        
        assert result["compliant"] is False
        assert any("L1-INDUSTRY-01" in v for v in result["violations"])
    
    def test_industry_passes_with_name(self):
        """Test valid Industry passes checks."""
        industry = Industry(
            name="Healthcare",
            entity_type="Industry",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = validate_constitutional_alignment(industry)
        assert result["compliant"] is True
