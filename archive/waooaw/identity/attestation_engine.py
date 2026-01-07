"""
Attestation Engine - Runtime attestation and verification for Platform CoE agents.

Provides runtime attestations that prove agent state, capabilities, and environment
at any point in time. Extends capability credentials with attestation claims.

Reference:
- Agent Architecture.md (Section 4: Attestations)
- AGENT_IDENTITY_BINDINGS.md (Attestation specifications)
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any
from cryptography.hazmat.primitives.asymmetric import ed25519

from waooaw.identity.vc_issuer import VerifiableCredential, get_vc_issuer
from waooaw.identity.did_service import get_did_service


@dataclass
class RuntimeAttestation:
    """
    Runtime attestation for an agent.
    
    Proves that an agent is running in a specific environment
    with specific capabilities at a specific time.
    
    Example:
    {
      "agent_did": "did:waooaw:wowdomain",
      "runtime_type": "kubernetes",
      "runtime_manifest": {
        "image_digest": "sha256:abc123...",
        "pod_id": "wowdomain-pod-xyz",
        "namespace": "waooaw-coe",
        "resource_limits": {"cpu": "1000m", "memory": "2Gi"}
      },
      "state": {
        "lifecycle": "active",
        "health": "healthy",
        "last_wake": "2025-12-29T10:00:00Z",
        "wake_count": 42
      },
      "capabilities": ["can:model-domain", "can:validate-ddd"],
      "timestamp": "2025-12-29T10:00:00Z",
      "signature": "z58DAdFfa9..."
    }
    """
    
    agent_did: str  # DID of agent being attested
    runtime_type: str  # kubernetes, serverless, edge, etc.
    runtime_manifest: Dict[str, Any]  # Runtime-specific details
    state: Dict[str, Any]  # Agent state (lifecycle, health, metrics)
    capabilities: List[str]  # Current capabilities
    timestamp: str  # ISO 8601 timestamp
    signature: Optional[str] = None  # Ed25519 signature
    issuer_did: Optional[str] = None  # DID of attester
    
    def to_dict(self, include_signature: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "agent_did": self.agent_did,
            "runtime_type": self.runtime_type,
            "runtime_manifest": self.runtime_manifest,
            "state": self.state,
            "capabilities": self.capabilities,
            "timestamp": self.timestamp
        }
        
        if include_signature and self.signature:
            data["signature"] = self.signature
            data["issuer_did"] = self.issuer_did
            
        return data
    
    def to_json(self, include_signature: bool = True) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(include_signature), indent=2, sort_keys=True)
    
    def get_canonical_form(self) -> bytes:
        """Get canonical form for signing (without signature)."""
        return self.to_json(include_signature=False).encode('utf-8')


@dataclass
class AttestationClaim:
    """
    A single attestation claim within a credential.
    
    Example:
    {
      "type": "RuntimeStateAttestation",
      "issued_at": "2025-12-29T10:00:00Z",
      "expires_at": "2025-12-29T10:01:00Z",
      "claims": {
        "runtime_type": "kubernetes",
        "health_status": "healthy",
        "capability_count": 5
      },
      "signature": "z58DAdFfa9..."
    }
    """
    
    claim_type: str  # Type of attestation
    issued_at: str  # ISO 8601 timestamp
    expires_at: str  # ISO 8601 timestamp (short-lived)
    claims: Dict[str, Any]  # Attestation claims
    signature: Optional[str] = None  # Ed25519 signature


class AttestationEngine:
    """
    Attestation Engine for runtime verification.
    
    Generates and verifies attestations for Platform CoE agents.
    Attestations are short-lived (1-5 minutes) and prove current state.
    """
    
    def __init__(self, attester_did: str = "did:waooaw:wowvision-prime"):
        """
        Initialize attestation engine.
        
        Args:
            attester_did: DID of the attestation issuer (default: WowVisionPrime)
        """
        self.attester_did = attester_did
        self.did_service = get_did_service()
        self.vc_issuer = get_vc_issuer()
        
    def create_runtime_attestation(
        self,
        agent_did: str,
        runtime_type: str,
        runtime_manifest: Dict[str, Any],
        agent_state: Dict[str, Any],
        capabilities: List[str]
    ) -> RuntimeAttestation:
        """
        Create runtime attestation for an agent.
        
        Args:
            agent_did: DID of agent to attest
            runtime_type: Type of runtime (kubernetes, serverless, etc.)
            runtime_manifest: Runtime-specific details (image digest, pod ID, etc.)
            agent_state: Current agent state (lifecycle, health, metrics)
            capabilities: Current capabilities
            
        Returns:
            Unsigned RuntimeAttestation
        """
        timestamp = datetime.now(UTC).isoformat()
        
        return RuntimeAttestation(
            agent_did=agent_did,
            runtime_type=runtime_type,
            runtime_manifest=runtime_manifest,
            state=agent_state,
            capabilities=capabilities,
            timestamp=timestamp
        )
    
    def sign_attestation(
        self,
        attestation: RuntimeAttestation,
        private_key: ed25519.Ed25519PrivateKey
    ) -> RuntimeAttestation:
        """
        Sign a runtime attestation.
        
        Args:
            attestation: Unsigned attestation
            private_key: Attester's private key
            
        Returns:
            Signed RuntimeAttestation
        """
        # Get canonical form
        canonical = attestation.get_canonical_form()
        
        # Sign with private key
        signature = private_key.sign(canonical)
        
        # Encode signature as multibase (z prefix for base58-btc)
        signature_multibase = f"z{signature.hex()}"
        
        # Create signed attestation
        attestation.signature = signature_multibase
        attestation.issuer_did = self.attester_did
        
        return attestation
    
    def issue_runtime_attestation(
        self,
        agent_did: str,
        runtime_type: str,
        runtime_manifest: Dict[str, Any],
        agent_state: Dict[str, Any],
        capabilities: List[str],
        private_key: ed25519.Ed25519PrivateKey
    ) -> RuntimeAttestation:
        """
        Complete attestation issuance flow (create + sign).
        
        Args:
            agent_did: DID of agent to attest
            runtime_type: Type of runtime
            runtime_manifest: Runtime-specific details
            agent_state: Current agent state
            capabilities: Current capabilities
            private_key: Attester's private key
            
        Returns:
            Signed RuntimeAttestation
        """
        # Create unsigned attestation
        attestation = self.create_runtime_attestation(
            agent_did=agent_did,
            runtime_type=runtime_type,
            runtime_manifest=runtime_manifest,
            agent_state=agent_state,
            capabilities=capabilities
        )
        
        # Sign attestation
        signed_attestation = self.sign_attestation(attestation, private_key)
        
        return signed_attestation
    
    def extend_credential_with_attestation(
        self,
        credential: VerifiableCredential,
        attestation: RuntimeAttestation
    ) -> VerifiableCredential:
        """
        Extend a capability credential with runtime attestation.
        
        Args:
            credential: Existing capability credential
            attestation: Runtime attestation to add
            
        Returns:
            Credential with attestation claim added
        """
        # Add attestation as additional claim
        if "attestation" not in credential.credential_subject:
            credential.credential_subject["attestation"] = []
        
        attestation_claim = {
            "type": "RuntimeStateAttestation",
            "issued_at": attestation.timestamp,
            "runtime_type": attestation.runtime_type,
            "runtime_manifest": attestation.runtime_manifest,
            "state": attestation.state,
            "signature": attestation.signature,
            "issuer_did": attestation.issuer_did
        }
        
        credential.credential_subject["attestation"].append(attestation_claim)
        
        return credential
    
    def verify_runtime_attestation(
        self,
        attestation: RuntimeAttestation,
        issuer_public_key: ed25519.Ed25519PublicKey,
        max_age_seconds: int = 300  # 5 minutes default
    ) -> tuple[bool, Optional[str]]:
        """
        Verify a runtime attestation.
        
        Args:
            attestation: Attestation to verify
            issuer_public_key: Public key of attester
            max_age_seconds: Maximum age of attestation in seconds
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if attestation is signed
            if not attestation.signature:
                return False, "Attestation is not signed"
            
            # Check attestation age
            timestamp = datetime.fromisoformat(attestation.timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.now(UTC) - timestamp).total_seconds()
            
            if age_seconds > max_age_seconds:
                return False, f"Attestation expired (age: {age_seconds:.0f}s, max: {max_age_seconds}s)"
            
            # Verify signature
            canonical = attestation.get_canonical_form()
            signature_hex = attestation.signature[1:]  # Strip 'z' prefix
            signature_bytes = bytes.fromhex(signature_hex)
            
            issuer_public_key.verify(signature_bytes, canonical)
            
            return True, None
            
        except Exception as e:
            return False, f"Attestation verification failed: {str(e)}"
    
    def create_attestation_claim(
        self,
        claim_type: str,
        claims: Dict[str, Any],
        validity_seconds: int = 60,
        private_key: Optional[ed25519.Ed25519PrivateKey] = None
    ) -> AttestationClaim:
        """
        Create a short-lived attestation claim.
        
        Args:
            claim_type: Type of attestation claim
            claims: Claims to attest
            validity_seconds: How long the claim is valid
            private_key: Optional private key for signing
            
        Returns:
            AttestationClaim (signed if private_key provided)
        """
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(seconds=validity_seconds)
        
        claim = AttestationClaim(
            claim_type=claim_type,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
            claims=claims
        )
        
        if private_key:
            # Sign claim
            canonical = json.dumps({
                "type": claim.claim_type,
                "issued_at": claim.issued_at,
                "expires_at": claim.expires_at,
                "claims": claim.claims
            }, sort_keys=True).encode('utf-8')
            
            signature = private_key.sign(canonical)
            claim.signature = f"z{signature.hex()}"
        
        return claim


# Singleton instance
_attestation_engine = None

def get_attestation_engine(attester_did: str = "did:waooaw:wowvision-prime") -> AttestationEngine:
    """Get singleton attestation engine instance."""
    global _attestation_engine
    if _attestation_engine is None:
        _attestation_engine = AttestationEngine(attester_did=attester_did)
    return _attestation_engine
