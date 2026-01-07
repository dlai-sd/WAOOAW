"""
Tests for Capability Validator.

Tests credential validation including signature verification,
expiration checking, revocation, and capability authorization.
"""

import pytest
from datetime import datetime, timezone, timedelta
from waooaw.identity.capability_validator import CapabilityValidator, get_capability_validator
from waooaw.identity.vc_issuer import VCIssuer, VerifiableCredential
from waooaw.identity.did_service import get_did_service


@pytest.fixture
def did_service():
    """Get DID service instance."""
    return get_did_service()


@pytest.fixture
def issuer_setup(did_service):
    """Create issuer DID and VC issuer."""
    did_doc, private_key = did_service.provision_agent_did("Test Issuer")
    vc_issuer = VCIssuer(issuer_did=did_doc.id)
    return did_doc, private_key, vc_issuer


@pytest.fixture
def subject_did(did_service):
    """Create subject DID."""
    did_doc, _ = did_service.provision_agent_did("Test Subject")
    return did_doc.id


@pytest.fixture
def validator():
    """Get capability validator instance."""
    return CapabilityValidator()


@pytest.fixture
def valid_credential(issuer_setup, subject_did):
    """Create a valid, signed credential."""
    did_doc, private_key, vc_issuer = issuer_setup
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:read", "can:write"],
        private_key=private_key,
        validity_days=30
    )
    
    return credential, did_doc


def test_validator_initialization(validator):
    """Test validator can be initialized."""
    assert validator is not None
    assert hasattr(validator, 'revoked_credentials')
    assert len(validator.revoked_credentials) == 0


def test_get_validator_singleton():
    """Test get_capability_validator returns singleton."""
    val1 = get_capability_validator()
    val2 = get_capability_validator()
    assert val1 is val2


def test_verify_signature_valid(validator, valid_credential):
    """Test signature verification with valid credential."""
    credential, issuer_did_doc = valid_credential
    
    is_valid, error = validator.verify_signature(credential, issuer_did_doc)
    
    assert is_valid
    assert error is None


def test_verify_signature_invalid_tampered_data(validator, valid_credential):
    """Test signature verification fails with tampered data."""
    credential, issuer_did_doc = valid_credential
    
    # Tamper with credential
    credential.credential_subject["capabilities"].append("can:hack")
    
    is_valid, error = validator.verify_signature(credential, issuer_did_doc)
    
    assert not is_valid
    assert error is not None
    assert "verification failed" in error.lower()


def test_verify_signature_missing_proof(validator, valid_credential):
    """Test signature verification fails without proof."""
    credential, issuer_did_doc = valid_credential
    
    # Remove proof
    credential.proof = None
    
    is_valid, error = validator.verify_signature(credential, issuer_did_doc)
    
    assert not is_valid
    assert error is not None
    assert "no proof" in error.lower()


def test_check_expiration_valid(validator, valid_credential):
    """Test expiration check with valid credential."""
    credential, _ = valid_credential
    
    is_valid, error = validator.check_expiration(credential)
    
    assert is_valid
    assert error is None


def test_check_expiration_expired(validator, issuer_setup, subject_did):
    """Test expiration check with expired credential."""
    did_doc, private_key, vc_issuer = issuer_setup
    
    # Create credential that expires in the past
    credential = vc_issuer.create_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        validity_days=-1  # Expired yesterday
    )
    credential = vc_issuer.sign_credential(credential, private_key)
    
    is_valid, error = validator.check_expiration(credential)
    
    assert not is_valid
    assert error is not None
    assert "expired" in error.lower()


def test_check_revocation_not_revoked(validator, valid_credential):
    """Test revocation check with non-revoked credential."""
    credential, _ = valid_credential
    
    is_valid, error = validator.check_revocation(credential)
    
    assert is_valid
    assert error is None


def test_check_revocation_revoked(validator, valid_credential):
    """Test revocation check with revoked credential."""
    credential, _ = valid_credential
    
    # Revoke the credential
    validator.revoke_credential(credential.id)
    
    is_valid, error = validator.check_revocation(credential)
    
    assert not is_valid
    assert error is not None
    assert "revoked" in error.lower()


def test_revoke_and_unrevoke(validator):
    """Test revoking and unrevoking credentials."""
    cred_id = "urn:uuid:test-123"
    
    # Revoke
    validator.revoke_credential(cred_id)
    assert cred_id in validator.revoked_credentials
    
    # Unrevoke
    validator.unrevoke_credential(cred_id)
    assert cred_id not in validator.revoked_credentials


def test_validate_credential_all_valid(validator, valid_credential):
    """Test complete credential validation with valid credential."""
    credential, issuer_did_doc = valid_credential
    
    is_valid, errors = validator.validate_credential(
        credential=credential,
        issuer_did_doc=issuer_did_doc
    )
    
    assert is_valid
    assert len(errors) == 0


def test_validate_credential_with_errors(validator, valid_credential):
    """Test validation catches multiple errors."""
    credential, issuer_did_doc = valid_credential
    
    # Tamper and revoke
    credential.credential_subject["capabilities"].append("can:evil")
    validator.revoke_credential(credential.id)
    
    is_valid, errors = validator.validate_credential(
        credential=credential,
        issuer_did_doc=issuer_did_doc
    )
    
    assert not is_valid
    assert len(errors) >= 2  # Signature + revocation errors


def test_has_capability_positive(validator, valid_credential):
    """Test checking for capability that exists."""
    credential, _ = valid_credential
    
    has_read = validator.has_capability(credential, "can:read")
    has_write = validator.has_capability(credential, "can:write")
    
    assert has_read
    assert has_write


def test_has_capability_negative(validator, valid_credential):
    """Test checking for capability that doesn't exist."""
    credential, _ = valid_credential
    
    has_delete = validator.has_capability(credential, "can:delete")
    has_execute = validator.has_capability(credential, "can:execute")
    
    assert not has_delete
    assert not has_execute


def test_validate_constraints_valid(validator, issuer_setup, subject_did):
    """Test constraint validation with valid constraints."""
    did_doc, private_key, vc_issuer = issuer_setup
    
    constraints = [
        {"rule": "max_operations", "value": 100},
        {"rule": "allowed_resources", "value": ["res-1", "res-2"]}
    ]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key,
        constraints=constraints
    )
    
    context = {
        "operation_count": 50,
        "resource": "res-1"
    }
    
    is_valid, error = validator.validate_constraints(credential, context)
    
    # Should pass (basic validation)
    assert is_valid
    assert error is None


def test_validate_constraints_no_constraints(validator, valid_credential):
    """Test constraint validation with no constraints."""
    credential, _ = valid_credential
    
    is_valid, error = validator.validate_constraints(credential, {})
    
    assert is_valid
    assert error is None


def test_signature_verification_wrong_issuer(validator, valid_credential, did_service):
    """Test signature verification fails with wrong issuer DID."""
    credential, _ = valid_credential
    
    # Create a different issuer
    wrong_issuer_doc, _ = did_service.provision_agent_did("Wrong Issuer")
    
    is_valid, error = validator.verify_signature(credential, wrong_issuer_doc)
    
    assert not is_valid
    assert error is not None


def test_multiple_revocations(validator):
    """Test revoking multiple credentials."""
    cred_ids = [f"urn:uuid:test-{i}" for i in range(5)]
    
    # Revoke all
    for cred_id in cred_ids:
        validator.revoke_credential(cred_id)
    
    assert len(validator.revoked_credentials) == 5
    
    # Unrevoke some
    validator.unrevoke_credential(cred_ids[0])
    validator.unrevoke_credential(cred_ids[2])
    
    assert len(validator.revoked_credentials) == 3
    assert cred_ids[1] in validator.revoked_credentials
    assert cred_ids[0] not in validator.revoked_credentials


def test_validation_with_context(validator, issuer_setup, subject_did):
    """Test validation with context for constraints."""
    did_doc, private_key, vc_issuer = issuer_setup
    
    constraints = [
        {"rule": "max_operations", "value": 10}
    ]
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:test"],
        private_key=private_key,
        constraints=constraints
    )
    
    context = {"operation_count": 5}
    
    is_valid, errors = validator.validate_credential(
        credential=credential,
        issuer_did_doc=did_doc,
        context=context
    )
    
    assert is_valid
    assert len(errors) == 0


def test_validator_handles_missing_fields(validator):
    """Test validator handles credentials with missing fields."""
    # Create incomplete credential
    credential = VerifiableCredential(
        id="urn:uuid:test",
        issuer="did:waooaw:test",
        issuance_date=datetime.now(timezone.utc).isoformat(),
        expiration_date=None,  # Missing expiration
        credential_subject={},
        proof=None
    )
    
    # Should handle gracefully
    is_valid, error = validator.check_expiration(credential)
    
    # Without expiration date, it should check if None
    # The current implementation should handle this
    assert error is not None or not is_valid  # Either error or not valid


def test_capability_string_matching(validator, issuer_setup, subject_did):
    """Test exact string matching for capabilities."""
    did_doc, private_key, vc_issuer = issuer_setup
    
    credential = vc_issuer.issue_capability_credential(
        subject_did=subject_did,
        capabilities=["can:read:resource-1", "can:write:resource-2"],
        private_key=private_key
    )
    
    # Exact matches
    assert validator.has_capability(credential, "can:read:resource-1")
    assert validator.has_capability(credential, "can:write:resource-2")
    
    # Partial matches should fail
    assert not validator.has_capability(credential, "can:read")
    assert not validator.has_capability(credential, "can:write")
    assert not validator.has_capability(credential, "resource-1")
