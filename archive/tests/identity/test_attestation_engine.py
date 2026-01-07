"""
Tests for AttestationEngine - Runtime attestation and short-lived claims.

Epic 2.3: Attestation System (v0.5.3)
"""

import pytest
import json
from datetime import datetime, timedelta, UTC
from cryptography.hazmat.primitives.asymmetric import ed25519
from waooaw.identity.did_service import DIDService
from waooaw.identity.did_registry import get_did_registry
from waooaw.identity.attestation_engine import (
    AttestationEngine,
    RuntimeAttestation,
    AttestationClaim,
    get_attestation_engine
)


@pytest.fixture
def did_service():
    """DID service fixture."""
    return DIDService()


@pytest.fixture
def did_registry():
    """DID registry fixture."""
    return get_did_registry()


@pytest.fixture
def attestation_engine():
    """Attestation engine fixture."""
    return AttestationEngine()


@pytest.fixture
def attester_did_doc(did_service, did_registry):
    """Create attester DID document."""
    did_doc, private_key = did_service.provision_agent_did("wowvision-prime")
    did_registry.register(did_doc)
    return did_doc, private_key


@pytest.fixture
def agent_did_doc(did_service, did_registry):
    """Create agent DID document."""
    did_doc, private_key = did_service.provision_agent_did("wowdomain")
    did_registry.register(did_doc)
    return did_doc, private_key


class TestRuntimeAttestation:
    """Test RuntimeAttestation dataclass."""
    
    def test_create_runtime_attestation(self):
        """Test: Create runtime attestation."""
        attestation = RuntimeAttestation(
            agent_did="did:waooaw:wowdomain",
            runtime_type="kubernetes",
            runtime_manifest={
                "image_digest": "sha256:abc123",
                "pod_id": "wowdomain-12345",
                "namespace": "waooaw-agents"
            },
            state={"lifecycle": "active", "health": "healthy"},
            capabilities=["can:model-domain", "can:validate-ddd"],
            timestamp=datetime.now(UTC).isoformat(),
            issuer_did="did:waooaw:wowvision-prime"
        )
        
        assert attestation.agent_did == "did:waooaw:wowdomain"
        assert attestation.runtime_type == "kubernetes"
        assert len(attestation.capabilities) == 2
        assert attestation.signature is None  # Not signed yet
    
    def test_attestation_to_dict(self):
        """Test: Convert attestation to dictionary."""
        attestation = RuntimeAttestation(
            agent_did="did:waooaw:test",
            runtime_type="serverless",
            runtime_manifest={"function_arn": "arn:aws:lambda:..."},
            state={"lifecycle": "active"},
            capabilities=["can:test"],
            timestamp=datetime.now(UTC).isoformat(),
            issuer_did="did:waooaw:issuer"
        )
        
        data = attestation.to_dict()
        
        assert isinstance(data, dict)
        assert data["agent_did"] == "did:waooaw:test"
        assert data["runtime_type"] == "serverless"
    
    def test_attestation_to_json(self):
        """Test: Convert attestation to JSON."""
        attestation = RuntimeAttestation(
            agent_did="did:waooaw:test",
            runtime_type="edge",
            runtime_manifest={},
            state={},
            capabilities=[],
            timestamp=datetime.now(UTC).isoformat(),
            issuer_did="did:waooaw:issuer"
        )
        
        json_str = attestation.to_json()
        
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["agent_did"] == "did:waooaw:test"
    
    def test_attestation_canonical_form(self):
        """Test: Get canonical form for signing."""
        attestation = RuntimeAttestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={},
            state={},
            capabilities=[],
            timestamp="2025-01-01T00:00:00Z",
            issuer_did="did:waooaw:issuer"
        )
        
        canonical = attestation.get_canonical_form()
        
        assert isinstance(canonical, bytes)
        assert b"did:waooaw:test" in canonical


class TestAttestationClaim:
    """Test AttestationClaim dataclass."""
    
    def test_create_attestation_claim(self):
        """Test: Create attestation claim."""
        now = datetime.now(UTC)
        claim = AttestationClaim(
            claim_type="capability_assertion",
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=60)).isoformat(),
            claims={"capability": "can:test", "scope": "read"},
            signature=None
        )
        
        assert claim.claim_type == "capability_assertion"
        assert "capability" in claim.claims
    
    def test_claim_to_dict(self):
        """Test: Convert claim to dictionary (using dataclass asdict)."""
        from dataclasses import asdict
        now = datetime.now(UTC)
        claim = AttestationClaim(
            claim_type="test_claim",
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=30)).isoformat(),
            claims={"test": "value"},
            signature=None
        )
        
        data = asdict(claim)
        
        assert isinstance(data, dict)
        assert data["claim_type"] == "test_claim"
        assert "issued_at" in data
        assert "expires_at" in data


class TestAttestationEngine:
    """Test AttestationEngine class."""
    
    def test_create_attestation_engine(self):
        """Test: Create attestation engine."""
        engine = AttestationEngine()
        
        assert engine.attester_did == "did:waooaw:wowvision-prime"
    
    def test_create_runtime_attestation(self, attestation_engine):
        """Test: Create unsigned runtime attestation."""
        attestation = attestation_engine.create_runtime_attestation(
            agent_did="did:waooaw:wowdomain",
            runtime_type="kubernetes",
            runtime_manifest={
                "image_digest": "sha256:abc123",
                "pod_id": "test-pod",
                "namespace": "test-ns"
            },
            agent_state={
                "lifecycle": "active",
                "health": "healthy",
                "uptime_seconds": 3600
            },
            capabilities=["can:model-domain", "can:validate-ddd"]
        )
        
        assert isinstance(attestation, RuntimeAttestation)
        assert attestation.agent_did == "did:waooaw:wowdomain"
        assert attestation.runtime_type == "kubernetes"
        assert len(attestation.capabilities) == 2
        assert attestation.signature is None  # Unsigned
    
    def test_sign_attestation(self, attestation_engine, attester_did_doc):
        """Test: Sign runtime attestation."""
        did_doc, private_key = attester_did_doc
        
        # Create unsigned attestation
        attestation = attestation_engine.create_runtime_attestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={},
            agent_state={"lifecycle": "active"},
            capabilities=["can:test"]
        )
        
        # Sign attestation
        signed_attestation = attestation_engine.sign_attestation(
            attestation,
            private_key
        )
        
        assert signed_attestation.signature is not None
        assert len(signed_attestation.signature) > 0
    
    def test_issue_runtime_attestation(self, attestation_engine, attester_did_doc):
        """Test: Issue complete runtime attestation (create + sign)."""
        did_doc, private_key = attester_did_doc
        
        attestation = attestation_engine.issue_runtime_attestation(
            agent_did="did:waooaw:wowdomain",
            runtime_type="kubernetes",
            runtime_manifest={
                "image_digest": "sha256:test123",
                "pod_id": "test-pod-456"
            },
            agent_state={"lifecycle": "active", "health": "healthy"},
            capabilities=["can:model-domain"],
            private_key=private_key
        )
        
        assert isinstance(attestation, RuntimeAttestation)
        assert attestation.signature is not None
        assert attestation.agent_did == "did:waooaw:wowdomain"
    
    def test_verify_runtime_attestation_valid(
        self,
        attestation_engine,
        attester_did_doc
    ):
        """Test: Verify valid runtime attestation."""
        did_doc, private_key = attester_did_doc
        
        # Issue attestation
        attestation = attestation_engine.issue_runtime_attestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={},
            agent_state={},
            capabilities=[],
            private_key=private_key
        )
        
        # Get public key
        public_key_multibase = did_doc.verification_methods[0]["publicKeyMultibase"]
        public_key_bytes = bytes.fromhex(public_key_multibase[1:])  # Remove 'z' prefix
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify attestation
        is_valid, error = attestation_engine.verify_runtime_attestation(
            attestation,
            public_key,
            max_age_seconds=300
        )
        
        assert is_valid is True
        assert error is None
    
    def test_verify_runtime_attestation_expired(
        self,
        attestation_engine,
        attester_did_doc
    ):
        """Test: Verify expired attestation fails."""
        did_doc, private_key = attester_did_doc
        
        # Issue attestation
        attestation = attestation_engine.issue_runtime_attestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={},
            agent_state={},
            capabilities=[],
            private_key=private_key
        )
        
        # Manually set old timestamp to make it expired
        old_timestamp = (datetime.now(UTC) - timedelta(seconds=400)).isoformat()
        attestation.timestamp = old_timestamp
        
        # Get public key
        public_key_multibase = did_doc.verification_methods[0]["publicKeyMultibase"]
        public_key_bytes = bytes.fromhex(public_key_multibase[1:])
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify attestation (should fail due to age)
        is_valid, error = attestation_engine.verify_runtime_attestation(
            attestation,
            public_key,
            max_age_seconds=300  # 5 minutes
        )
        
        assert is_valid is False
        assert "expired" in error.lower()
    
    def test_verify_runtime_attestation_invalid_signature(
        self,
        attestation_engine,
        attester_did_doc
    ):
        """Test: Verify attestation with invalid signature fails."""
        did_doc, private_key = attester_did_doc
        
        # Issue attestation
        attestation = attestation_engine.issue_runtime_attestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={},
            agent_state={},
            capabilities=[],
            private_key=private_key
        )
        
        # Tamper with signature
        attestation.signature = "invalid_signature_xyz"
        
        # Get public key
        public_key_multibase = did_doc.verification_methods[0]["publicKeyMultibase"]
        public_key_bytes = bytes.fromhex(public_key_multibase[1:])
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify attestation (should fail)
        is_valid, error = attestation_engine.verify_runtime_attestation(
            attestation,
            public_key
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_create_attestation_claim(self, attestation_engine, attester_did_doc):
        """Test: Create short-lived attestation claim."""
        did_doc, private_key = attester_did_doc
        
        claim = attestation_engine.create_attestation_claim(
            claim_type="capability_assertion",
            claims={
                "agent_did": "did:waooaw:test",
                "capability": "can:test",
                "scope": "read"
            },
            validity_seconds=60,
            private_key=private_key
        )
        
        assert isinstance(claim, AttestationClaim)
        assert claim.claim_type == "capability_assertion"
        assert claim.signature is not None
        
        # Check TTL
        issued = datetime.fromisoformat(claim.issued_at.replace('Z', '+00:00'))
        expires = datetime.fromisoformat(claim.expires_at.replace('Z', '+00:00'))
        ttl = (expires - issued).total_seconds()
        
        assert ttl == 60
    
    def test_extend_credential_with_attestation(
        self,
        attestation_engine,
        attester_did_doc
    ):
        """Test: Extend credential with runtime attestation."""
        from waooaw.identity.vc_issuer import VerifiableCredential
        
        did_doc, private_key = attester_did_doc
        
        # Create mock credential
        now = datetime.now(UTC)
        credential = VerifiableCredential(
            id="urn:uuid:test-cred-123",
            issuer="did:waooaw:issuer",
            issuance_date=now.isoformat(),
            expiration_date=(now + timedelta(days=365)).isoformat(),
            credential_subject={
                "id": "did:waooaw:test",
                "capabilities": ["can:test"]
            }
        )
        
        # Create attestation
        attestation = attestation_engine.issue_runtime_attestation(
            agent_did="did:waooaw:test",
            runtime_type="kubernetes",
            runtime_manifest={"pod_id": "test-pod"},
            agent_state={"lifecycle": "active"},
            capabilities=["can:test"],
            private_key=private_key
        )
        
        # Extend credential
        extended_credential = attestation_engine.extend_credential_with_attestation(
            credential,
            attestation
        )
        
        assert "attestation" in extended_credential.credential_subject
        attestation_data = extended_credential.credential_subject["attestation"]
        assert isinstance(attestation_data, list)
        assert len(attestation_data) > 0
        assert attestation_data[0]["runtime_type"] == "kubernetes"
    
    def test_multiple_runtime_types(self, attestation_engine, attester_did_doc):
        """Test: Create attestations for different runtime types."""
        did_doc, private_key = attester_did_doc
        
        runtime_types = ["kubernetes", "serverless", "edge"]
        
        for runtime_type in runtime_types:
            attestation = attestation_engine.issue_runtime_attestation(
                agent_did=f"did:waooaw:{runtime_type}-agent",
                runtime_type=runtime_type,
                runtime_manifest={"type": runtime_type},
                agent_state={"lifecycle": "active"},
                capabilities=[f"can:{runtime_type}"],
                private_key=private_key
            )
            
            assert attestation.runtime_type == runtime_type
            assert attestation.signature is not None


class TestAttestationSingleton:
    """Test attestation engine singleton."""
    
    def test_get_attestation_engine_singleton(self):
        """Test: Singleton returns same instance."""
        engine1 = get_attestation_engine()
        engine2 = get_attestation_engine()
        
        assert engine1 is engine2
    
    def test_singleton_attester_did(self):
        """Test: Singleton uses default attester DID."""
        engine = get_attestation_engine()
        
        assert engine.attester_did == "did:waooaw:wowvision-prime"
