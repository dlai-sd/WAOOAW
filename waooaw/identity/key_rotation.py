"""
Key Rotation System - Automated 90-day key rotation with credential re-issuance.

Implements:
- Automated rotation cycles (90/180 days based on agent type)
- Credential re-issuance workflow
- Key deprecation support
- Rotation metadata tracking

Part of Epic 2.3: Attestation System (v0.5.3)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from waooaw.identity.did_service import DIDService, DIDDocument
from waooaw.identity.did_registry import DIDRegistry
from waooaw.identity.vc_issuer import VCIssuer, VerifiableCredential

logger = logging.getLogger(__name__)


@dataclass
class KeyRotationRecord:
    """
    Record of a key rotation event.
    
    Attributes:
        agent_did: DID of agent whose key was rotated
        old_key_id: ID of previous verification method
        new_key_id: ID of new verification method
        rotation_date: When rotation occurred
        reason: Reason for rotation (scheduled, compromised, manual)
        grace_period_end: Date when old key becomes invalid
        credentials_reissued: Number of credentials re-issued
        metadata: Additional metadata
    """
    
    agent_did: str
    old_key_id: str
    new_key_id: str
    rotation_date: str  # ISO 8601
    reason: str  # scheduled, compromised, manual
    grace_period_end: str  # ISO 8601
    credentials_reissued: int = 0
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "agent_did": self.agent_did,
            "old_key_id": self.old_key_id,
            "new_key_id": self.new_key_id,
            "rotation_date": self.rotation_date,
            "reason": self.reason,
            "grace_period_end": self.grace_period_end,
            "credentials_reissued": self.credentials_reissued,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class RotationPolicy:
    """
    Key rotation policy for an agent.
    
    Attributes:
        agent_did: DID of agent
        rotation_interval_days: Days between rotations (90 or 180)
        last_rotation: Last rotation date
        next_rotation: Next scheduled rotation date
        grace_period_days: Days old key remains valid (default 7)
        auto_rotate: Whether to auto-rotate (default True)
        key_type: Type of key (Ed25519, RSA-4096)
    """
    
    agent_did: str
    rotation_interval_days: int  # 90 or 180
    last_rotation: str  # ISO 8601
    next_rotation: str  # ISO 8601
    grace_period_days: int = 7
    auto_rotate: bool = True
    key_type: str = "Ed25519"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "agent_did": self.agent_did,
            "rotation_interval_days": self.rotation_interval_days,
            "last_rotation": self.last_rotation,
            "next_rotation": self.next_rotation,
            "grace_period_days": self.grace_period_days,
            "auto_rotate": self.auto_rotate,
            "key_type": self.key_type
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'RotationPolicy':
        """Create from dictionary."""
        return RotationPolicy(**data)


class KeyRotationManager:
    """
    Manager for automated key rotation.
    
    Responsibilities:
    - Schedule key rotations based on policy
    - Execute key rotation (generate new key, update DID document)
    - Re-issue credentials with new key
    - Track rotation history
    - Handle grace periods (old key valid for N days)
    
    Default Policies:
    - Security-critical agents (WowSecurity): 90 days
    - Standard agents: 180 days
    - Grace period: 7 days
    """
    
    def __init__(
        self,
        did_service: DIDService,
        did_registry: DIDRegistry,
        vc_issuer: VCIssuer
    ):
        """
        Initialize key rotation manager.
        
        Args:
            did_service: DID service for key generation
            did_registry: Registry for DID document updates
            vc_issuer: VC issuer for credential re-issuance
        """
        self.did_service = did_service
        self.did_registry = did_registry
        self.vc_issuer = vc_issuer
        
        # Rotation policies (agent_did -> RotationPolicy)
        self._policies: Dict[str, RotationPolicy] = {}
        
        # Rotation history (agent_did -> List[KeyRotationRecord])
        self._history: Dict[str, List[KeyRotationRecord]] = {}
        
        # Active credentials that need re-issuance (agent_did -> List[VerifiableCredential])
        self._credentials_cache: Dict[str, List[VerifiableCredential]] = {}
        
        logger.info("KeyRotationManager initialized")
    
    def register_rotation_policy(
        self,
        agent_did: str,
        rotation_interval_days: int = 180,
        grace_period_days: int = 7,
        auto_rotate: bool = True,
        key_type: str = "Ed25519"
    ) -> RotationPolicy:
        """
        Register rotation policy for agent.
        
        Args:
            agent_did: DID of agent
            rotation_interval_days: Days between rotations (90 or 180)
            grace_period_days: Days old key remains valid
            auto_rotate: Whether to auto-rotate
            key_type: Type of key
            
        Returns:
            RotationPolicy object
        """
        now = datetime.now(UTC)
        last_rotation = now.isoformat()
        next_rotation = (now + timedelta(days=rotation_interval_days)).isoformat()
        
        policy = RotationPolicy(
            agent_did=agent_did,
            rotation_interval_days=rotation_interval_days,
            last_rotation=last_rotation,
            next_rotation=next_rotation,
            grace_period_days=grace_period_days,
            auto_rotate=auto_rotate,
            key_type=key_type
        )
        
        self._policies[agent_did] = policy
        logger.info(f"Registered rotation policy for {agent_did}: {rotation_interval_days} days")
        
        return policy
    
    def get_rotation_policy(self, agent_did: str) -> Optional[RotationPolicy]:
        """
        Get rotation policy for agent.
        
        Args:
            agent_did: DID of agent
            
        Returns:
            RotationPolicy if registered, None otherwise
        """
        return self._policies.get(agent_did)
    
    def list_rotation_policies(self) -> List[RotationPolicy]:
        """
        List all rotation policies.
        
        Returns:
            List of RotationPolicy objects
        """
        return list(self._policies.values())
    
    def is_rotation_due(self, agent_did: str) -> bool:
        """
        Check if key rotation is due for agent.
        
        Args:
            agent_did: DID of agent
            
        Returns:
            True if rotation is due, False otherwise
        """
        policy = self._policies.get(agent_did)
        if not policy:
            return False
        
        now = datetime.now(UTC)
        next_rotation = datetime.fromisoformat(policy.next_rotation.replace('Z', '+00:00'))
        
        return now >= next_rotation
    
    def list_agents_due_for_rotation(self) -> List[str]:
        """
        List all agents due for key rotation.
        
        Returns:
            List of agent DIDs
        """
        return [
            agent_did
            for agent_did in self._policies.keys()
            if self.is_rotation_due(agent_did)
        ]
    
    def rotate_agent_key(
        self,
        agent_did: str,
        reason: str = "scheduled",
        grace_period_days: Optional[int] = None
    ) -> Tuple[DIDDocument, ed25519.Ed25519PrivateKey, KeyRotationRecord]:
        """
        Rotate agent's key.
        
        Steps:
        1. Generate new Ed25519 key pair
        2. Get current DID document
        3. Add new verification method
        4. Update DID document in registry
        5. Create rotation record
        6. Update rotation policy
        
        Args:
            agent_did: DID of agent
            reason: Reason for rotation
            grace_period_days: Override grace period (uses policy default if None)
            
        Returns:
            Tuple of (updated_did_document, new_private_key, rotation_record)
        """
        logger.info(f"🔄 Rotating key for {agent_did} (reason: {reason})")
        
        # Get current DID document
        current_did_doc = self.did_registry.get(agent_did)
        if not current_did_doc:
            raise ValueError(f"DID document not found: {agent_did}")
        
        # Get rotation policy
        policy = self._policies.get(agent_did)
        if not policy:
            raise ValueError(f"No rotation policy registered for {agent_did}")
        
        # Generate new key pair
        new_private_key, new_public_key = self.did_service.generate_key_pair()
        
        # Get old key ID
        old_key_id = current_did_doc.verification_methods[0]["id"] if current_did_doc.verification_methods else None
        
        # Create new verification method
        new_key_id = f"{agent_did}#key-{len(current_did_doc.verification_methods) + 1}"
        new_verification_method = {
            "id": new_key_id,
            "type": "Ed25519VerificationKey2020",
            "controller": agent_did,
            "publicKeyMultibase": self.did_service.public_key_to_multibase(new_public_key)
        }
        
        # Update DID document
        current_did_doc.verification_methods.insert(0, new_verification_method)  # New key first
        current_did_doc.updated = datetime.now(UTC).isoformat()
        
        # Register updated DID document
        self.did_registry.register(current_did_doc)
        
        # Create rotation record
        now = datetime.now(UTC)
        grace_days = grace_period_days if grace_period_days is not None else policy.grace_period_days
        grace_period_end = (now + timedelta(days=grace_days)).isoformat()
        
        rotation_record = KeyRotationRecord(
            agent_did=agent_did,
            old_key_id=old_key_id or "none",
            new_key_id=new_key_id,
            rotation_date=now.isoformat(),
            reason=reason,
            grace_period_end=grace_period_end,
            credentials_reissued=0,  # Will be updated during re-issuance
            metadata={
                "key_type": policy.key_type,
                "rotation_interval_days": policy.rotation_interval_days
            }
        )
        
        # Store rotation record
        if agent_did not in self._history:
            self._history[agent_did] = []
        self._history[agent_did].append(rotation_record)
        
        # Update rotation policy
        policy.last_rotation = now.isoformat()
        policy.next_rotation = (now + timedelta(days=policy.rotation_interval_days)).isoformat()
        
        logger.info(f"✅ Key rotated for {agent_did}: {old_key_id} → {new_key_id}")
        logger.info(f"   Grace period ends: {grace_period_end}")
        logger.info(f"   Next rotation: {policy.next_rotation}")
        
        return current_did_doc, new_private_key, rotation_record
    
    def reissue_credentials(
        self,
        agent_did: str,
        credentials: List[VerifiableCredential],
        new_private_key: ed25519.Ed25519PrivateKey
    ) -> List[VerifiableCredential]:
        """
        Re-issue credentials with new key after rotation.
        
        Args:
            agent_did: DID of agent (credential issuer)
            credentials: List of credentials to re-issue
            new_private_key: New private key for signing
            
        Returns:
            List of re-issued credentials
        """
        logger.info(f"🔄 Re-issuing {len(credentials)} credentials for {agent_did}")
        
        reissued = []
        
        for credential in credentials:
            # Create new credential with same data
            new_credential = self.vc_issuer.issue_capability_credential(
                subject_did=credential.credential_subject.get("id"),
                capabilities=credential.credential_subject.get("capabilities", []),
                private_key=new_private_key,
                validity_days=365,  # Reset to 1 year
                constraints=credential.credential_subject.get("constraints")
            )
            
            reissued.append(new_credential)
            logger.debug(f"   Re-issued credential {new_credential.id}")
        
        logger.info(f"✅ Re-issued {len(reissued)} credentials")
        
        return reissued
    
    def deprecate_old_key(
        self,
        agent_did: str,
        key_id: str
    ) -> DIDDocument:
        """
        Deprecate old key after grace period.
        
        Removes verification method from DID document.
        
        Args:
            agent_did: DID of agent
            key_id: ID of key to deprecate
            
        Returns:
            Updated DID document
        """
        logger.info(f"🗑️  Deprecating key {key_id} for {agent_did}")
        
        # Get DID document
        did_doc = self.did_registry.get(agent_did)
        if not did_doc:
            raise ValueError(f"DID document not found: {agent_did}")
        
        # Remove old verification method
        did_doc.verification_methods = [
            vm for vm in did_doc.verification_methods
            if vm["id"] != key_id
        ]
        
        did_doc.updated = datetime.now(UTC).isoformat()
        
        # Update registry
        self.did_registry.register(did_doc)
        
        logger.info(f"✅ Key deprecated: {key_id}")
        
        return did_doc
    
    def get_rotation_history(
        self,
        agent_did: str,
        limit: int = 10
    ) -> List[KeyRotationRecord]:
        """
        Get rotation history for agent.
        
        Args:
            agent_did: DID of agent
            limit: Maximum number of records to return
            
        Returns:
            List of KeyRotationRecord objects (most recent first)
        """
        history = self._history.get(agent_did, [])
        return history[-limit:][::-1]  # Last N, reversed
    
    def export_rotation_metadata(self) -> Dict[str, any]:
        """
        Export rotation metadata for persistence.
        
        Returns:
            Dictionary with policies, history
        """
        return {
            "policies": {
                agent_did: policy.to_dict()
                for agent_did, policy in self._policies.items()
            },
            "history": {
                agent_did: [record.to_dict() for record in records]
                for agent_did, records in self._history.items()
            },
            "exported_at": datetime.now(UTC).isoformat()
        }
    
    def import_rotation_metadata(self, data: Dict[str, any]) -> None:
        """
        Import rotation metadata from persistence.
        
        Args:
            data: Dictionary with policies, history
        """
        # Import policies
        if "policies" in data:
            for agent_did, policy_dict in data["policies"].items():
                policy = RotationPolicy.from_dict(policy_dict)
                self._policies[agent_did] = policy
        
        # Import history
        if "history" in data:
            for agent_did, records in data["history"].items():
                self._history[agent_did] = [
                    KeyRotationRecord(**record)
                    for record in records
                ]
        
        logger.info(f"Imported rotation metadata: {len(self._policies)} policies, {sum(len(h) for h in self._history.values())} history records")


# Singleton instance
_key_rotation_manager: Optional[KeyRotationManager] = None


def get_key_rotation_manager(
    did_service: Optional[DIDService] = None,
    did_registry: Optional[DIDRegistry] = None,
    vc_issuer: Optional[VCIssuer] = None
) -> KeyRotationManager:
    """
    Get singleton KeyRotationManager instance.
    
    Args:
        did_service: DID service (required for first call)
        did_registry: DID registry (required for first call)
        vc_issuer: VC issuer (required for first call)
        
    Returns:
        KeyRotationManager instance
    """
    global _key_rotation_manager
    
    if _key_rotation_manager is None:
        if not all([did_service, did_registry, vc_issuer]):
            raise ValueError("First call to get_key_rotation_manager requires did_service, did_registry, and vc_issuer")
        
        _key_rotation_manager = KeyRotationManager(
            did_service=did_service,
            did_registry=did_registry,
            vc_issuer=vc_issuer
        )
    
    return _key_rotation_manager
