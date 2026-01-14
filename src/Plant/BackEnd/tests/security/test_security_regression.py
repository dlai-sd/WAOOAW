"""
Security Regression Tests

Tests for security vulnerabilities and regressions.
Validates:
- SQL injection prevention
- XSS prevention
- Authentication/authorization
- Data validation
- Cryptographic operations
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.skill import Skill
from security.cryptography import generate_rsa_keypair, sign_data, verify_signature
from security.hash_chain import validate_chain
from core.security import create_access_token, verify_token


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_name_field(self, async_session: AsyncSession):
        """Test that SQL injection in name field is prevented."""
        import uuid
        malicious_name = f"'; DROP TABLE base_entity; -- {uuid.uuid4()}"
        
        skill = Skill(
            name=malicious_name,
            description="SQL injection test",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="sql_v1",
            hash_chain_sha256=["hash1"],
        )
        
        # Should successfully insert without executing SQL
        async_session.add(skill)
        await async_session.flush()  # Use flush instead of commit for test isolation
        
        # Verify data is stored safely
        assert skill.name == malicious_name
        assert skill.id is not None
        
        # Rollback will happen automatically in fixture
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_query_parameter(self, async_session: AsyncSession):
        """Test SQL injection prevention in query filters."""
        # This would be dangerous if not using parameterized queries
        malicious_category = "technical' OR '1'='1"
        
        # SQLAlchemy should parameterize this automatically
        from sqlalchemy import select
        stmt = select(Skill).where(Skill.category == malicious_category)
        result = await async_session.execute(stmt)
        skills = result.scalars().all()
        
        # Should return 0 results (no match) instead of all results
        assert len(skills) == 0


class TestXSSPrevention:
    """Test XSS attack prevention."""
    
    @pytest.mark.asyncio
    async def test_xss_in_description_field(self, async_session: AsyncSession):
        """Test that XSS payloads are stored safely."""
        import uuid
        xss_payload = "<script>alert('XSS')</script>"
        
        skill = Skill(
            name=f"XSSTest_{uuid.uuid4()}",
            description=xss_payload,
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="xss_v1",
            hash_chain_sha256=["hash1"],
        )
        
        async_session.add(skill)
        await async_session.flush()
        
        # Payload should be stored as-is (sanitization happens at API layer)
        assert skill.description == xss_payload
        assert "<script>" in skill.description


class TestAuthenticationSecurity:
    """Test authentication and JWT security."""
    
    def test_jwt_token_expiration_respected(self):
        """Test that expired tokens are rejected."""
        from datetime import timedelta
        
        # Create token that expires immediately
        token = create_access_token(
            {"sub": "test_user"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Verify should fail
        decoded = verify_token(token)
        assert decoded is None  # Expired token should be rejected
    
    def test_jwt_token_signature_validation(self):
        """Test that tampered tokens are rejected."""
        token = create_access_token({"sub": "user123"})
        
        # Tamper with token
        parts = token.split(".")
        tampered_token = parts[0] + ".TAMPERED." + parts[2]
        
        decoded = verify_token(tampered_token)
        assert decoded is None  # Tampered token should be rejected
    
    def test_jwt_token_payload_integrity(self):
        """Test that token payload cannot be modified."""
        original_data = {"sub": "user123", "role": "user"}
        token = create_access_token(original_data)
        
        # Decode should return original data
        decoded = verify_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "user"


class TestCryptographicOperations:
    """Test cryptographic operation security."""
    
    def test_rsa_signature_cannot_be_reused(self):
        """Test that signatures are unique and cannot be reused."""
        private_key, public_key = generate_rsa_keypair()
        
        data1 = "Message 1"
        data2 = "Message 2"
        
        signature1 = sign_data(data1, private_key)
        signature2 = sign_data(data2, private_key)
        
        # Signatures should be different
        assert signature1 != signature2
        
        # Signature from data1 should not verify data2
        assert verify_signature(data1, signature1, public_key) is True
        assert verify_signature(data2, signature1, public_key) is False
    
    def test_hash_chain_tampering_detection(self):
        """Test that hash chain detects tampering."""
        amendments = [
            {"field": "value1"},
            {"field": "value2"},
            {"field": "value3"},
        ]
        
        # Build valid chain
        from security.hash_chain import calculate_sha256, create_hash_link
        hashes = []
        for i, amendment in enumerate(amendments):
            if i == 0:
                hash_val = calculate_sha256(str(amendment))
            else:
                hash_val = create_hash_link(hashes[i-1], str(amendment))
            hashes.append(hash_val)
        
        # Validate original chain
        result = validate_chain(amendments, hashes)
        assert result["intact"] is True
        
        # Tamper with middle amendment
        tampered_amendments = amendments.copy()
        tampered_amendments[1] = {"field": "TAMPERED"}
        
        # Validation should fail
        result = validate_chain(tampered_amendments, hashes)
        assert result["intact"] is False
        assert result["broken_at_index"] == 1


class TestDataValidation:
    """Test data validation and sanitization."""
    
    @pytest.mark.asyncio
    async def test_entity_type_validation(self):
        """Test that invalid entity types are rejected."""
        from validators.constitutional_validator import validate_constitutional_alignment
        
        skill = Skill(
            name="TestSkill",
            description="Test",
            category="invalid_category",  # Invalid category
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="val_v1",
            hash_chain_sha256=["hash1"],
        )
        
        result = validate_constitutional_alignment(skill)
        assert result["compliant"] is False
        assert any("L1-SKILL-03" in v for v in result["violations"])
    
    @pytest.mark.asyncio
    async def test_required_field_validation(self):
        """Test that required fields are enforced."""
        from validators.constitutional_validator import validate_constitutional_alignment
        
        skill = Skill(
            name="",  # Empty name (required)
            description="Test",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="val_v1",
            hash_chain_sha256=["hash1"],
        )
        
        result = validate_constitutional_alignment(skill)
        assert result["compliant"] is False
        assert any("L1-SKILL-01" in v for v in result["violations"])


class TestAppendOnlyEnforcement:
    """Test append-only pattern enforcement (no UPDATE/DELETE)."""
    
    @pytest.mark.asyncio
    async def test_entity_supersession_instead_of_update(self, async_session: AsyncSession):
        """Test that entities use supersession instead of UPDATE."""
        import uuid
        skill = Skill(
            name=f"OriginalSkill_{uuid.uuid4()}",
            description="Original description",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="v1",
            hash_chain_sha256=["hash1"],
        )
        
        async_session.add(skill)
        await async_session.flush()
        original_id = skill.id
        
        # Instead of UPDATE, create evolution
        skill.evolve({"description": "Updated description"})
        
        # Original entity should remain unchanged in DB
        assert skill.id == original_id
        assert len(skill.amendment_history) == 1
    
    @pytest.mark.asyncio
    async def test_status_change_instead_of_delete(self, async_session: AsyncSession):
        """Test that soft delete (status change) is used instead of DELETE."""
        import uuid
        skill = Skill(
            name=f"ToDeleteSkill_{uuid.uuid4()}",
            description="Will be soft deleted",
            category="technical",
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash="v1",
            hash_chain_sha256=["hash1"],
        )
        
        async_session.add(skill)
        await async_session.flush()
        
        # Soft delete by changing status
        skill.status = "deleted"
        await async_session.flush()
        
        # Entity should still exist in DB
        from sqlalchemy import select
        stmt = select(Skill).where(Skill.id == skill.id)
        result = await async_session.execute(stmt)
        deleted_skill = result.scalar_one()
        
        assert deleted_skill is not None
        assert deleted_skill.status == "deleted"
