"""
Unit tests for constitutional alignment validators
"""

import pytest

from models.base_entity import BaseEntity
from models.skill import Skill
from validators.constitutional_validator import validate_constitutional_alignment


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
