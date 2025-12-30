"""
DID Service - Decentralized Identifier provisioning and management.

Generates and manages DIDs for all WAOOAW agents following the format:
did:waooaw:{agent-name}

Example: did:waooaw:wowvision-prime
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


@dataclass
class DIDDocument:
    """
    DID Document as per W3C DID specification.
    
    Reference: https://www.w3.org/TR/did-core/
    """
    
    id: str  # did:waooaw:agent-name
    controller: str  # did:waooaw:wowvision-prime (guardian)
    created: str  # ISO 8601 timestamp
    updated: str  # ISO 8601 timestamp
    verification_methods: List[Dict] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    capability_invocation: List[str] = field(default_factory=list)
    service_endpoints: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert DID document to dictionary."""
        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/ed25519-2020/v1"
            ],
            "id": self.id,
            "controller": self.controller,
            "created": self.created,
            "updated": self.updated,
            "verificationMethod": self.verification_methods,
            "authentication": self.authentication,
            "capabilityInvocation": self.capability_invocation,
            "service": self.service_endpoints
        }
    
    def to_json(self) -> str:
        """Convert DID document to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class DIDService:
    """
    DID Service for generating and managing decentralized identifiers.
    
    Responsibilities:
    - Generate unique DIDs for agents
    - Create DID documents with public keys
    - Sign DID documents
    - Verify DID document signatures
    - Resolve DIDs to documents
    """
    
    def __init__(self):
        """Initialize DID service."""
        self.namespace = "waooaw"
        self.guardian_did = "did:waooaw:wowvision-prime"
        
    def generate_did(self, agent_name: str) -> str:
        """
        Generate DID for agent.
        
        Args:
            agent_name: Agent name (e.g., "WowVisionPrime", "WowDomain")
            
        Returns:
            DID string (e.g., "did:waooaw:wowvision-prime")
        """
        # Convert agent name to kebab-case
        name_kebab = agent_name.replace(" ", "-").lower()
        return f"did:{self.namespace}:{name_kebab}"
    
    def generate_key_pair(self) -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Generate Ed25519 key pair for agent.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    def public_key_to_multibase(self, public_key: ed25519.Ed25519PublicKey) -> str:
        """
        Convert public key to multibase format.
        
        Args:
            public_key: Ed25519 public key
            
        Returns:
            Multibase-encoded public key string
        """
        # Serialize public key to bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Multibase base58-btc encoding (z prefix)
        # For simplicity, using hex encoding here
        # In production, use proper multibase library
        return f"z{public_key_bytes.hex()}"
    
    def create_did_document(
        self,
        agent_name: str,
        public_key: ed25519.Ed25519PublicKey,
        service_endpoint: Optional[str] = None
    ) -> DIDDocument:
        """
        Create DID document for agent.
        
        Args:
            agent_name: Agent name
            public_key: Agent's public key
            service_endpoint: Optional service endpoint URL
            
        Returns:
            DID document
        """
        did = self.generate_did(agent_name)
        now = datetime.now(UTC).isoformat()
        
        # Verification method (public key)
        verification_method_id = f"{did}#key-1"
        verification_method = {
            "id": verification_method_id,
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": self.public_key_to_multibase(public_key)
        }
        
        # Service endpoints
        services = []
        if service_endpoint:
            services.append({
                "id": f"{did}#agent-service",
                "type": "AgentService",
                "serviceEndpoint": service_endpoint
            })
        
        return DIDDocument(
            id=did,
            controller=self.guardian_did,  # WowVisionPrime controls all agents
            created=now,
            updated=now,
            verification_methods=[verification_method],
            authentication=[verification_method_id],
            capability_invocation=[verification_method_id],
            service_endpoints=services
        )
    
    def provision_agent_did(
        self,
        agent_name: str,
        service_endpoint: Optional[str] = None
    ) -> tuple[DIDDocument, ed25519.Ed25519PrivateKey]:
        """
        Provision complete DID for agent (generate keys + create document).
        
        Args:
            agent_name: Agent name
            service_endpoint: Optional service endpoint URL
            
        Returns:
            Tuple of (DID document, private key)
        """
        # Generate key pair
        private_key, public_key = self.generate_key_pair()
        
        # Create DID document
        did_doc = self.create_did_document(agent_name, public_key, service_endpoint)
        
        return did_doc, private_key
    
    def resolve_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve DID to document (placeholder - needs registry integration).
        
        Args:
            did: DID to resolve
            
        Returns:
            DID document if found, None otherwise
        """
        # TODO: Integrate with DIDRegistry
        # For now, return None
        return None
    
    def verify_did_signature(self, did_document: DIDDocument, signature: bytes, message: bytes) -> bool:
        """
        Verify signature on message using DID document's public key.
        
        Args:
            did_document: DID document containing public key
            signature: Signature to verify
            message: Original message that was signed
            
        Returns:
            True if signature valid, False otherwise
        """
        try:
            # Extract public key from DID document
            if not did_document.verification_methods:
                return False
            
            verification_method = did_document.verification_methods[0]
            public_key_multibase = verification_method["publicKeyMultibase"]
            
            # Decode multibase (strip 'z' prefix and decode hex)
            public_key_bytes = bytes.fromhex(public_key_multibase[1:])
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            public_key.verify(signature, message)
            return True
            
        except Exception:
            return False
    
    def get_did_fingerprint(self, did_document: DIDDocument) -> str:
        """
        Get fingerprint (hash) of DID document for integrity verification.
        
        Args:
            did_document: DID document
            
        Returns:
            SHA-256 hex digest of document
        """
        doc_json = did_document.to_json()
        return hashlib.sha256(doc_json.encode()).hexdigest()


# Singleton instance
_did_service = None

def get_did_service() -> DIDService:
    """Get singleton DID service instance."""
    global _did_service
    if _did_service is None:
        _did_service = DIDService()
    return _did_service
