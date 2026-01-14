"""
Unit tests for BaseEntity - 7-section architecture + cryptography
"""

import pytest
import hashlib
import json
from datetime import datetime

from models.base_entity import BaseEntity
from core.exceptions import ConstitutionalAlignmentError


class TestBaseEntityCreation:
    """Test BaseEntity instantiation and initialization."""
    
    def test_base_entity_creates_with_all_sections(self):
        """Test that BaseEntity initializes all 7 sections."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="initial_hash",
        )
        
        # Section 1: Identity
        assert entity.id is not None
        assert entity.entity_type == "TestEntity"
        
        # Section 2: Lifecycle
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert entity.status == "active"
        
        # Section 3: Versioning
        assert entity.version_hash == "initial_hash"
        assert isinstance(entity.amendment_history, list)
        
        # Section 4: Constitutional Alignment
        assert isinstance(entity.l0_compliance_status, dict)
        assert entity.amendment_alignment == "aligned"
        
        # Section 5: Audit Trail
        assert entity.append_only is True
        assert isinstance(entity.hash_chain_sha256, list)
        assert entity.tamper_proof is True
        
        # Section 6: Metadata
        assert isinstance(entity.tags, list)
        assert isinstance(entity.custom_attributes, dict)
        
        # Section 7: Relationships
        assert entity.governance_agent_id == "genesis"
        assert isinstance(entity.child_ids, list)


class TestValidateSelf:
    """Test L0 constitutional compliance validation."""
    
    def test_validate_self_passes_for_compliant_entity(self):
        """Test that compliant entity passes all L0 checks."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash123",
            hash_chain_sha256=["hash123"],
        )
        
        result = entity.validate_self()
        
        assert result["compliant"] is True
        assert result["checks"]["l0_01"] is True  # governance_agent_id present
        assert result["checks"]["l0_02"] is True  # amendment_history tracked
        assert result["checks"]["l0_03"] is True  # append_only enforced
        assert result["checks"]["l0_04"] is True  # hash_chain present
        assert result["checks"]["l0_05"] is True  # version_hash set
        assert len(result["violations"]) == 0
    
    def test_validate_self_fails_without_governance_agent(self):
        """Test that missing governance_agent_id causes L0-01 violation."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id=None,
            version_hash="hash123",
        )
        
        result = entity.validate_self()
        
        assert result["compliant"] is False
        assert result["checks"]["l0_01"] is False
        assert any("L0-01" in v for v in result["violations"])


class TestEvolve:
    """Test entity evolution (versioning + amendments)."""
    
    def test_evolve_creates_new_version_hash(self):
        """Test that evolve() generates new version hash."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="initial_hash",
            hash_chain_sha256=[],
        )
        
        changes = {"field": "new_value"}
        new_hash = entity.evolve(changes)
        
        assert new_hash != "initial_hash"
        assert entity.version_hash == new_hash
        assert len(entity.hash_chain_sha256) == 1
        assert entity.hash_chain_sha256[0] == new_hash
    
    def test_evolve_appends_amendment_history(self):
        """Test that amendments are appended to history."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="initial_hash",
            amendment_history=[],
        )
        
        changes = {"field": "new_value"}
        entity.evolve(changes)
        
        assert len(entity.amendment_history) == 1
        assert entity.amendment_history[0]["data"] == changes
        assert "timestamp" in entity.amendment_history[0]


class TestCryptography:
    """Test RSA signing and verification."""
    
    def test_sign_and_verify_amendment(self, rsa_keypair):
        """Test that amendment signatures can be verified."""
        private_pem, public_pem = rsa_keypair
        
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash123",
            amendment_history=[],
        )
        
        # Create amendment
        entity.evolve({"field": "value"})
        
        # Sign amendment
        signature = entity.sign_amendment(private_pem)
        assert signature is not None
        assert len(signature) > 0
        
        # Verify signature
        is_valid = entity.verify_amendment(public_pem)
        assert is_valid is True
    
    def test_verify_fails_with_wrong_key(self, rsa_keypair):
        """Test that signature verification fails with wrong public key."""
        from security.cryptography import generate_rsa_keypair
        
        private_pem, _ = rsa_keypair
        _, wrong_public_pem = generate_rsa_keypair()  # Different keypair
        
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash123",
            amendment_history=[],
        )
        
        entity.evolve({"field": "value"})
        entity.sign_amendment(private_pem)
        
        # Verify with wrong key
        is_valid = entity.verify_amendment(wrong_public_pem)
        assert is_valid is False


class TestHashChainIntegrity:
    """Test audit trail hash chain validation."""
    
    def test_hash_chain_integrity_valid(self):
        """Test that valid hash chain passes integrity check."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash1",
            amendment_history=[{"data": {"field": "value1"}}],
            hash_chain_sha256=[
                hashlib.sha256(json.dumps({"field": "value1"}, sort_keys=True).encode()).hexdigest()
            ],
        )
        
        result = entity.get_hash_chain_integrity()
        
        assert result["intact"] is True
        assert result["broken_at_index"] is None
    
    def test_hash_chain_detects_tampering(self):
        """Test that tampered hash chain is detected."""
        entity = BaseEntity(
            entity_type="TestEntity",
            governance_agent_id="genesis",
            version_hash="hash1",
            amendment_history=[{"data": {"field": "value1"}}],
            hash_chain_sha256=["tampered_hash"],  # Wrong hash
        )
        
        result = entity.get_hash_chain_integrity()
        
        assert result["intact"] is False
        assert result["broken_at_index"] is not None
