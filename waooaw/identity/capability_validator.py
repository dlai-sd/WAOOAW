"""
Capability Validator - Verify capability credentials at runtime.

Validates verifiable credentials for agent capabilities including:
- Signature verification
- Expiration checking
- Constraint validation
- Revocation status
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519

from waooaw.identity.vc_issuer import VerifiableCredential
from waooaw.identity.did_service import DIDDocument


class CapabilityValidator:
    """
    Validates capability credentials at runtime.
    
    Used by WowSecurity to authorize agent actions based on
    their capability credentials.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.revoked_credentials: set = set()  # In-memory revocation list
        
    def verify_signature(
        self,
        credential: VerifiableCredential,
        issuer_did_doc: DIDDocument
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify credential signature.
        
        Args:
            credential: Credential to verify
            issuer_did_doc: Issuer's DID document (contains public key)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if credential has proof
            if not credential.proof:
                return False, "Credential has no proof"
            
            # Extract signature from proof
            proof_value = credential.proof.get("proofValue", "")
            if not proof_value.startswith("z"):
                return False, "Invalid proof value format"
            
            # Decode signature (strip 'z' prefix and decode hex)
            signature_bytes = bytes.fromhex(proof_value[1:])
            
            # Get canonical form (unsigned credential) - already bytes
            canonical = credential.get_canonical_form()
            
            # Extract public key from issuer's DID document
            if not issuer_did_doc.verification_methods:
                return False, "Issuer has no verification methods"
            
            verification_method = issuer_did_doc.verification_methods[0]
            public_key_multibase = verification_method["publicKeyMultibase"]
            
            # Decode public key
            public_key_bytes = bytes.fromhex(public_key_multibase[1:])
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            public_key.verify(signature_bytes, canonical)
            
            return True, None
            
        except Exception as e:
            return False, f"Signature verification failed: {str(e)}"
    
    def check_expiration(
        self,
        credential: VerifiableCredential
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if credential is expired.
        
        Args:
            credential: Credential to check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            now = datetime.now(UTC)
            
            # Parse expiration date
            expiration = datetime.fromisoformat(credential.expiration_date.replace('Z', '+00:00'))
            
            if now > expiration:
                return False, f"Credential expired on {credential.expiration_date}"
            
            return True, None
            
        except Exception as e:
            return False, f"Expiration check failed: {str(e)}"
    
    def check_revocation(
        self,
        credential: VerifiableCredential
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if credential is revoked.
        
        Args:
            credential: Credential to check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if credential.id in self.revoked_credentials:
            return False, "Credential has been revoked"
        
        return True, None
    
    def validate_constraints(
        self,
        credential: VerifiableCredential,
        context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate credential constraints.
        
        Args:
            credential: Credential to validate
            context: Runtime context for constraint evaluation
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        constraints = credential.credential_subject.get("constraints", [])
        
        if not constraints:
            return True, None
        
        # TODO: Implement constraint validation logic
        # For now, just check that constraints exist and are well-formed
        for constraint in constraints:
            if not isinstance(constraint, dict):
                return False, "Invalid constraint format"
            
            if "rule" not in constraint:
                return False, "Constraint missing 'rule' field"
        
        return True, None
    
    def validate_credential(
        self,
        credential: VerifiableCredential,
        issuer_did_doc: DIDDocument,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Perform complete credential validation.
        
        Args:
            credential: Credential to validate
            issuer_did_doc: Issuer's DID document
            context: Runtime context
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check signature
        sig_valid, sig_error = self.verify_signature(credential, issuer_did_doc)
        if not sig_valid:
            errors.append(sig_error)
        
        # Check expiration
        exp_valid, exp_error = self.check_expiration(credential)
        if not exp_valid:
            errors.append(exp_error)
        
        # Check revocation
        rev_valid, rev_error = self.check_revocation(credential)
        if not rev_valid:
            errors.append(rev_error)
        
        # Validate constraints
        const_valid, const_error = self.validate_constraints(credential, context)
        if not const_valid:
            errors.append(const_error)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def has_capability(
        self,
        credential: VerifiableCredential,
        required_capability: str
    ) -> bool:
        """
        Check if credential grants a specific capability.
        
        Args:
            credential: Credential to check
            required_capability: Capability to look for (e.g., "can:model-domain")
            
        Returns:
            True if credential grants capability, False otherwise
        """
        capabilities = credential.credential_subject.get("capabilities", [])
        return required_capability in capabilities
    
    def revoke_credential(self, credential_id: str) -> None:
        """
        Add credential to revocation list.
        
        Args:
            credential_id: ID of credential to revoke
        """
        self.revoked_credentials.add(credential_id)
    
    def unrevoke_credential(self, credential_id: str) -> None:
        """
        Remove credential from revocation list.
        
        Args:
            credential_id: ID of credential to unrevoke
        """
        self.revoked_credentials.discard(credential_id)


# Singleton instance
_capability_validator = None

def get_capability_validator() -> CapabilityValidator:
    """Get singleton capability validator instance."""
    global _capability_validator
    if _capability_validator is None:
        _capability_validator = CapabilityValidator()
    return _capability_validator
