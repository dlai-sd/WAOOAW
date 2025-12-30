"""
Tests for VC (Verifiable Credential) Issuer.

Tests credential creation, signing, revocation, and validation
according to W3C Verifiable Credentials Data Model.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from waooaw.identity.vc_issuer import VCIssuer, VerifiableCredential, get_vc_issuer
from waooaw.identity.did_service import get_did_service


@pytest.fixture
def did_service():
    """Get DID service instance."""
    return get_did_service()


@pytest.fixture
def issuer_did_and_key(did_service):
    """Create issuer DID and private key."""
    did_doc, private_key = did_service.provision_agent_did("Test Issuer")
    return did_doc, private_key


@pytest.fixture
def subject_did(did_service):
    """Create subject DID."""
    did_doc, _ = did_service.provision_agent_did("Test Subject")
    return did_doc.id


@pytest.fixture
def vc_issuer(issuer_did_and_key):
    """Get VC issuer with test issuer DID."""
    did_doc, _ = issuer_did_and_key
    return VCIssuer(issuer_did=did_doc.id)


def test_vc_issuer_initialization(vc_issuer):
    """Test VC issuer can be initialized."""
    assert vc_issuer is not None
    assert vc_issuer.issuer_did.startswith("did:waooaw:")


def test_get_vc_issuer_singleton():
    """Test get_vc_issuer returns singleton instance."""
    issuer1 = get_vc_issuer()
    issuer2 = get_vc_issuer()
    assert issuer1 is issuer2
    assert issuer1.issuer_did == "did:waooaw:wowvision-prime"


def test_create_capability_credential(vc_issuer, subject_did):
    """Test creating unsigned capability credential."""
    capabilities = ["can:read", "can:write", "can:execute"]
    
    credential = vc_issuer.create_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        validity_days=30
    )
    
    assert credential is not None
    assert credential.issuer == vc_issuer.issuer_did
    assert credential.credential_subject["id"] == subject_did
    assert credential.credential_subject["capabilities"] == capabilities
    assert credential.proof is None  # Unsigned
    
    # Check dates
    assert credential.issuance_date is not None
    assert credential.expiration_date is not None
    
    # Verify expiration is ~30 days from issuance
    issuance = datetime.fromisoformat(credential.issuance_date.replace('Z', '+00:00'))
    expiration = datetime.fromisoformat(credential.expiration_date.replace('Z', '+00:00'))
    delta = (expiration - issuance).days
    assert 29 <= delta <= 31  # Allow for timezone/rounding


def test_sign_credential(vc_issuer, subject_did, issuer_did_and_key):
    """Test signing a credential with Ed25519 key."""
    _, private_key = issuer_did_and_key
    capabilities = ["can:test"]
    
    # Create unsigned credential
    credential = vc_issuer.create_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities
    )
    assert credential.proof is None
    
    # Sign credential
    signed = vc_issuer.sign_credential(credential, private_key)
    
    assert signed.proof is not None
    assert signed.proof["type"] == "Ed25519Signature2020"
    assert signed.proof["verificationMethod"] == f"{vc_issuer.issuer_did}#key-1"
    assert signed.proof["proofPurpose"] == "assertionMethod"
    assert "proofValue" in signed.proof
    assert signed.proof["proofValue"].startswith("z")  # Multibase encoded


def test_issue_capability_credential(vc_issuer, subject_did, issuer_did_and_key):
    """Test complete credential issuance flow."""
    _, private_key = issuer_did_and_key
    capabilities = ["can:manage-domain", "can:emit-events"]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        private_key=private_key,
        validity_days=90
    )
    
    # Verify complete credential
    assert credential.id.startswith("urn:uuid:")
    assert credential.issuer == vc_issuer.issuer_did
    assert credential.credential_subject["id"] == subject_did
    assert credential.credential_subject["capabilities"] == capabilities
    assert credential.proof is not None
    assert "VerifiableCredential" in credential.type
    assert "AgentCapabilityCredential" in credential.type


def test_credential_with_constraints(vc_issuer, subject_did, issuer_did_and_key):
    """Test creating credential with constraints."""
    _, private_key = issuer_did_and_key
    capabilities = ["can:read"]
    constraints = {
        "max_operations_per_hour": 100,
        "allowed_resources": ["resource-1", "resource-2"]
    }
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        private_key=private_key,
        constraints=constraints
    )
    
    assert credential.credential_subject.get("constraints") == constraints


def test_revoke_credential(vc_issuer):
    """Test credential revocation."""
    credential_id = "urn:uuid:test-credential-123"
    
    revocation = vc_issuer.revoke_credential(
        credential_id=credential_id,
        reason="Testing revocation"
    )
    
    assert revocation["credentialId"] == credential_id
    assert revocation["reason"] == "Testing revocation"
    assert "revokedAt" in revocation
    assert revocation["issuer"] == vc_issuer.issuer_did


def test_credential_to_dict(vc_issuer, subject_did, issuer_did_and_key):
    """Test credential serialization to dict."""
    _, private_key = issuer_did_and_key
    capabilities = ["can:test"]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        private_key=private_key
    )
    
    cred_dict = credential.to_dict()
    
    assert isinstance(cred_dict, dict)
    assert "@context" in cred_dict
    assert "id" in cred_dict
    assert "type" in cred_dict
    assert "issuer" in cred_dict
    assert "credentialSubject" in cred_dict
    assert "proof" in cred_dict


def test_credential_to_json(vc_issuer, subject_did, issuer_did_and_key):
    """Test credential serialization to JSON."""
    _, private_key = issuer_did_and_key
    capabilities = ["can:test"]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        private_key=private_key
    )
    
    cred_json = credential.to_json()
    
    assert isinstance(cred_json, str)
    parsed = json.loads(cred_json)
    assert parsed["issuer"] == vc_issuer.issuer_did


def test_credential_canonical_form(vc_issuer, subject_did):
    """Test credential canonical form for signing."""
    capabilities = ["can:test"]
    
    credential = vc_issuer.create_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities
    )
    
    canonical = credential.get_canonical_form()
    
    assert isinstance(canonical, bytes)
    assert len(canonical) > 0


def test_multiple_capabilities(vc_issuer, subject_did, issuer_did_and_key):
    """Test issuing credential with many capabilities."""
    _, private_key = issuer_did_and_key
    capabilities = [
        "can:read:resource-1",
        "can:write:resource-1",
        "can:delete:resource-1",
        "can:read:resource-2",
        "can:write:resource-2",
        "can:execute:script-1",
        "can:manage:agents"
    ]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=capabilities,
        private_key=private_key
    )
    
    assert len(credential.credential_subject["capabilities"]) == 7
    assert all(cap in credential.credential_subject["capabilities"] for cap in capabilities)


def test_credential_expiration_dates(vc_issuer, subject_did, issuer_did_and_key):
    """Test different validity periods."""
    _, private_key = issuer_did_and_key
    
    # Short validity
    cred_7d = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key,
        validity_days=7
    )
    
    # Long validity
    cred_365d = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key,
        validity_days=365
    )
    
    # Parse dates
    exp_7d = datetime.fromisoformat(cred_7d.expiration_date.replace('Z', '+00:00'))
    exp_365d = datetime.fromisoformat(cred_365d.expiration_date.replace('Z', '+00:00'))
    
    # Verify difference
    delta = (exp_365d - exp_7d).days
    assert 357 <= delta <= 359  # ~358 days difference


def test_credential_id_uniqueness(vc_issuer, subject_did, issuer_did_and_key):
    """Test that each credential gets a unique ID."""
    _, private_key = issuer_did_and_key
    
    cred1 = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key
    )
    
    cred2 = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key
    )
    
    assert cred1.id != cred2.id
