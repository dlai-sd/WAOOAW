"""
Verifiable Credentials (VC) Issuer - Issue and manage capability credentials.

Implements W3C Verifiable Credentials Data Model for agent capabilities.
Reference: https://www.w3.org/TR/vc-data-model/
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


@dataclass
class VerifiableCredential:
    """
    W3C Verifiable Credential for agent capabilities.
    
    Example:
    {
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      "type": ["VerifiableCredential", "AgentCapabilityCredential"],
      "issuer": "did:waooaw:wowvision-prime",
      "issuanceDate": "2025-12-29T10:00:00Z",
      "expirationDate": "2026-12-29T10:00:00Z",
      "credentialSubject": {
        "id": "did:waooaw:wowdomain",
        "capabilities": ["can:model-domain", "can:validate-ddd"]
      },
      "proof": {
        "type": "Ed25519Signature2020",
        "created": "2025-12-29T10:00:00Z",
        "verificationMethod": "did:waooaw:wowvision-prime#key-1",
        "proofPurpose": "assertionMethod",
        "proofValue": "z58DAdFfa9..."
      }
    }
    """
    
    id: str  # Unique credential ID
    issuer: str  # DID of issuer (WowVisionPrime)
    issuance_date: str  # ISO 8601 timestamp
    expiration_date: str  # ISO 8601 timestamp
    credential_subject: Dict[str, Any]  # Subject DID and capabilities
    proof: Optional[Dict[str, str]] = None  # Digital signature
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/2018/credentials/v1",
        "https://waooaw.com/credentials/v1"
    ])
    credential_type: List[str] = field(default_factory=lambda: [
        "VerifiableCredential",
        "AgentCapabilityCredential"
    ])
    
    @property
    def type(self) -> List[str]:
        """Get credential type (alias for credential_type)."""
        return self.credential_type
    
    def to_dict(self, include_proof: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "@context": self.context,
            "id": self.id,
            "type": self.credential_type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "expirationDate": self.expiration_date,
            "credentialSubject": self.credential_subject
        }
        
        if include_proof and self.proof:
            data["proof"] = self.proof
            
        return data
    
    def to_json(self, include_proof: bool = True) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(include_proof), indent=2, sort_keys=True)
    
    def get_canonical_form(self) -> bytes:
        """Get canonical form for signing (without proof)."""
        return self.to_json(include_proof=False).encode('utf-8')


class VCIssuer:
    """
    Verifiable Credential Issuer.
    
    Issues capability credentials for Platform CoE agents.
    All credentials are signed by WowVisionPrime (the guardian).
    """
    
    def __init__(self, issuer_did: str = "did:waooaw:wowvision-prime"):
        """
        Initialize VC issuer.
        
        Args:
            issuer_did: DID of the issuer (default: WowVisionPrime)
        """
        self.issuer_did = issuer_did
        self.verification_method = f"{issuer_did}#key-1"
        
    def create_capability_credential(
        self,
        subject_did: str,
        capabilities: List[str],
        validity_days: int = 365,
        constraints: Optional[List[Dict[str, str]]] = None
    ) -> VerifiableCredential:
        """
        Create capability credential for an agent.
        
        Args:
            subject_did: DID of the agent receiving capabilities
            capabilities: List of capabilities (e.g., ["can:model-domain"])
            validity_days: Days until expiration (default: 365)
            constraints: Optional list of constraints
            
        Returns:
            VerifiableCredential (unsigned)
        """
        now = datetime.now(UTC)
        expiration = now + timedelta(days=validity_days)
        
        # Generate unique credential ID
        credential_id = f"urn:uuid:{hashlib.sha256(f'{subject_did}{now.isoformat()}'.encode()).hexdigest()[:32]}"
        
        # Build credential subject
        credential_subject = {
            "id": subject_did,
            "capabilities": capabilities
        }
        
        if constraints:
            credential_subject["constraints"] = constraints
        
        return VerifiableCredential(
            id=credential_id,
            issuer=self.issuer_did,
            issuance_date=now.isoformat(),
            expiration_date=expiration.isoformat(),
            credential_subject=credential_subject
        )
    
    def sign_credential(
        self,
        credential: VerifiableCredential,
        private_key: ed25519.Ed25519PrivateKey
    ) -> VerifiableCredential:
        """
        Sign a credential with issuer's private key.
        
        Args:
            credential: Unsigned credential
            private_key: Issuer's private key
            
        Returns:
            Signed credential
        """
        # Get canonical form (without proof)
        canonical = credential.get_canonical_form()
        
        # Sign with private key (canonical is already bytes)
        signature = private_key.sign(canonical)
        
        # Encode signature as multibase (z prefix for base58-btc)
        # For simplicity, using hex encoding here
        signature_multibase = f"z{signature.hex()}"
        
        # Create proof object
        proof = {
            "type": "Ed25519Signature2020",
            "created": datetime.now(UTC).isoformat(),
            "verificationMethod": self.verification_method,
            "proofPurpose": "assertionMethod",
            "proofValue": signature_multibase
        }
        
        # Add proof to credential
        credential.proof = proof
        
        return credential
    
    def issue_capability_credential(
        self,
        subject_did: str,
        capabilities: List[str],
        private_key: ed25519.Ed25519PrivateKey,
        validity_days: int = 365,
        constraints: Optional[List[Dict[str, str]]] = None
    ) -> VerifiableCredential:
        """
        Create and sign a capability credential (complete flow).
        
        Args:
            subject_did: DID of the agent
            capabilities: List of capabilities
            private_key: Issuer's private key for signing
            validity_days: Days until expiration
            constraints: Optional constraints
            
        Returns:
            Signed verifiable credential
        """
        # Create credential
        credential = self.create_capability_credential(
            subject_did=subject_did,
            capabilities=capabilities,
            validity_days=validity_days,
            constraints=constraints
        )
        
        # Sign credential
        signed_credential = self.sign_credential(credential, private_key)
        
        return signed_credential
    
    def revoke_credential(self, credential_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a credential revocation record.
        
        Args:
            credential_id: ID of credential to revoke
            reason: Reason for revocation (optional)
            
        Returns:
            Revocation record
        """
        result = {
            "credentialId": credential_id,
            "issuer": self.issuer_did,
            "revokedAt": datetime.now(UTC).isoformat()
        }
        if reason:
            result["reason"] = reason
        else:
            result["reason"] = "revoked"
        return result


# Singleton instance
_vc_issuer = None

def get_vc_issuer(issuer_did: str = "did:waooaw:wowvision-prime") -> VCIssuer:
    """Get singleton VC issuer instance."""
    global _vc_issuer
    if _vc_issuer is None:
        _vc_issuer = VCIssuer(issuer_did)
    return _vc_issuer
