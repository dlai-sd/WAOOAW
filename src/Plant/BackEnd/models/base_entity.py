"""
BaseEntity - Universal root class for all Plant entities
Implements 7-section architecture for L0/L1 constitutional alignment

SECTIONS:
1. identity: uuid, entity_type, external_id
2. lifecycle: created_at, updated_at, deleted_at, status
3. versioning: version_hash, amendment_history, evolution_markers
4. constitutional_alignment: l0_compliance_status, amendment_alignment, drift_detector
5. audit_trail: append_only marker, hash_chain_sha256, tamper_proof flag
6. metadata: tags, custom_attributes, governance_notes
7. relationships: parent_id, child_ids, governance_agent_id
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, String, DateTime, JSON, UUID, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from pydantic import BaseModel, Field

from core.database import Base
from core.logging import get_logger

logger = get_logger(__name__)


class BaseEntity(Base):
    """
    Universal root class for all Plant entities.
    
    Inherits from SQLAlchemy Base (ORM mapping) and provides all 7 sections
    required by the Plant blueprint.
    
    Sections:
        - IDENTITY (Section 1): uuid, entity_type, external_id
        - LIFECYCLE (Section 2): created_at, updated_at, deleted_at, status
        - VERSIONING (Section 3): version_hash, amendment_history, evolution_markers
        - CONSTITUTIONAL_ALIGNMENT (Section 4): l0_compliance_status, amendment_alignment, drift_detector
        - AUDIT_TRAIL (Section 5): append_only, hash_chain_sha256, tamper_proof
        - METADATA (Section 6): tags, custom_attributes, governance_notes
        - RELATIONSHIPS (Section 7): parent_id, child_ids, governance_agent_id
    
    Example:
        >>> skill = Skill(name="Python", category="technical")
        >>> skill.validate_self()  # Verify L0/L1 compliance
        >>> skill.evolve({"name": "Python 3.11"})  # Create new version
        >>> skill.sign_amendment(private_key)  # RSA signature
        >>> skill.verify_amendment(public_key)  # Third-party verification
    
    Constraints:
        - All entities must pass validate_self() before persistence
        - Amendment history is append-only (no updates to past amendments)
        - Hash chain must be immutable (SHA-256 links)
        - Governance agent ID tracks all changes
    """
    
    __tablename__ = "base_entity"
    __abstract__ = False  # Enable ORM table creation
    
    # ========== SECTION 1: IDENTITY ==========
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="UUID primary key (unique across all entities)"
    )
    
    entity_type = Column(
        String(50),
        nullable=False,
        doc="Type of entity (Skill, JobRole, Team, Agent, Industry)"
    )
    
    external_id = Column(
        String(255),
        nullable=True,
        unique=True,
        doc="Optional external identifier (for integrations)"
    )
    
    # ========== SECTION 2: LIFECYCLE ==========
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Creation timestamp (immutable)"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp"
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        doc="Soft delete timestamp (RLS policy respects this)"
    )
    
    status = Column(
        String(20),
        nullable=False,
        default="active",
        doc="Entity status (active, archived, deleted)"
    )
    
    # ========== SECTION 3: VERSIONING ==========
    version_hash = Column(
        String(64),
        nullable=False,
        default="initial",
        doc="SHA-256 hash of current version (for change detection)"
    )
    
    amendment_history = Column(
        JSON,
        nullable=False,
        default=lambda: [],
        doc="Array of amendments [{timestamp, change_type, data, signature_hash}]"
    )
    
    evolution_markers = Column(
        JSON,
        nullable=False,
        default=lambda: {},
        doc="Track breaking vs non-breaking changes"
    )
    
    # ========== SECTION 4: CONSTITUTIONAL ALIGNMENT ==========
    l0_compliance_status = Column(
        JSON,
        nullable=False,
        default=lambda: {},
        doc="L0 checks {l0_01: bool, l0_02: bool, ...} (governance, history, append-only, etc)"
    )
    
    amendment_alignment = Column(
        String(20),
        nullable=False,
        default="aligned",
        doc="Amendment alignment status (aligned, drifted, requires_review)"
    )
    
    drift_detector = Column(
        JSON,
        nullable=False,
        default=lambda: {},
        doc="Drift detection metrics (for embeddings: stability_score, last_regenerated)"
    )
    
    # ========== SECTION 5: AUDIT TRAIL ==========
    append_only = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Append-only flag (enforced by RLS trigger)"
    )
    
    hash_chain_sha256 = Column(
        ARRAY(String),
        nullable=False,
        default=lambda: [],
        doc="SHA-256 chain of all historical versions [hash0, hash1, ...]"
    )
    
    tamper_proof = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Tamper-proof flag (RLS policy prevents UPDATE/DELETE)"
    )
    
    # ========== SECTION 6: METADATA ==========
    tags = Column(
        ARRAY(String),
        nullable=False,
        default=lambda: [],
        doc="Tags for categorization and filtering"
    )
    
    custom_attributes = Column(
        JSON,
        nullable=False,
        default=lambda: {},
        doc="Custom fields (entity-specific, stored as JSON)"
    )
    
    governance_notes = Column(
        Text,
        nullable=True,
        doc="Notes from governance agents (audit trail)"
    )
    
    # ========== SECTION 7: RELATIONSHIPS ==========
    parent_id = Column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="Parent entity ID (for hierarchies)"
    )
    
    child_ids = Column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        default=lambda: [],
        doc="Child entity IDs"
    )
    
    governance_agent_id = Column(
        String(100),
        nullable=False,
        default="genesis",
        doc="ID of governance agent responsible for this entity"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_base_entity_entity_type", "entity_type"),
        Index("ix_base_entity_created_at", "created_at"),
        Index("ix_base_entity_status", "status"),
        Index("ix_base_entity_governance_agent_id", "governance_agent_id"),
    )

    __mapper_args__ = {
        "polymorphic_on": entity_type,
        "polymorphic_identity": "BaseEntity",
        "with_polymorphic": "*",
    }
    
    def __init__(self, **kwargs):
        """Initialize BaseEntity with proper defaults for non-database instantiation."""
        super().__init__(**kwargs)
        
        # Initialize id if not provided
        if not hasattr(self, 'id') or self.id is None:
            self.id = uuid.uuid4()
        
        # Initialize status if not provided (and not explicitly set to None)
        if not hasattr(self, 'status') or (self.status is None and 'status' not in kwargs):
            self.status = "active"
        
        # Do NOT override governance_agent_id if explicitly passed as None in kwargs
        if not hasattr(self, 'governance_agent_id') or (self.governance_agent_id is None and 'governance_agent_id' not in kwargs):
            self.governance_agent_id = "genesis"
        
        # Initialize version_hash if not provided (and not explicitly set to None)
        if not hasattr(self, 'version_hash') or (self.version_hash is None and 'version_hash' not in kwargs):
            self.version_hash = "initial"
        
        # Initialize amendment_alignment if not provided
        if not hasattr(self, 'amendment_alignment') or (self.amendment_alignment is None and 'amendment_alignment' not in kwargs):
            self.amendment_alignment = "aligned"
        
        # Initialize boolean flags (only if not explicitly provided)
        if not hasattr(self, 'append_only') or (self.append_only is None and 'append_only' not in kwargs):
            self.append_only = True
        if not hasattr(self, 'tamper_proof') or (self.tamper_proof is None and 'tamper_proof' not in kwargs):
            self.tamper_proof = True
        
        # Initialize lists and dicts that might be None
        if not hasattr(self, 'amendment_history') or self.amendment_history is None:
            self.amendment_history = []
        if not hasattr(self, 'evolution_markers') or self.evolution_markers is None:
            self.evolution_markers = {}
        if not hasattr(self, 'l0_compliance_status') or self.l0_compliance_status is None:
            self.l0_compliance_status = {}
        if not hasattr(self, 'drift_detector') or self.drift_detector is None:
            self.drift_detector = {}
        if not hasattr(self, 'hash_chain_sha256') or self.hash_chain_sha256 is None:
            self.hash_chain_sha256 = []
        if not hasattr(self, 'tags') or self.tags is None:
            self.tags = []
        if not hasattr(self, 'custom_attributes') or self.custom_attributes is None:
            self.custom_attributes = {}
        if not hasattr(self, 'child_ids') or self.child_ids is None:
            self.child_ids = []
        
        # Initialize timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def validate_self(self) -> Dict[str, Any]:
        """
        Validate entity against L0/L1 constitutional principles.
        
        Runs on property access (continuous validation).
        
        L0 Checks:
        - L0-01: governance_agent_id present (governance chain)
        - L0-02: amendment_history tracked (no deletions)
        - L0-03: append-only enforced (no manual UPDATEs to past)
        - L0-04: supersession chain preserved (entity evolution trackable)
        - L0-05: compliance gate possible (validation result exportable)
        
        Returns:
            Dict[str, Any]: Compliance status {
                "compliant": bool,
                "checks": {"l0_01": bool, "l0_02": bool, ...},
                "violations": [list of violation descriptions]
            }
        
        Example:
            >>> result = entity.validate_self()
            >>> if not result["compliant"]:
            ...     raise ConstitutionalAlignmentError(result["violations"])
        """
        violations = []
        checks = {}
        
        # L0-01: governance_agent_id present
        checks["l0_01"] = bool(self.governance_agent_id)
        if not checks["l0_01"]:
            violations.append("L0-01: governance_agent_id missing")
        
        # L0-02: amendment_history tracked
        checks["l0_02"] = isinstance(self.amendment_history, list)
        if not checks["l0_02"]:
            violations.append("L0-02: amendment_history not tracked")
        
        # L0-03: append-only enforced
        checks["l0_03"] = self.append_only
        if not checks["l0_03"]:
            violations.append("L0-03: append-only not enforced")
        
        # L0-04: supersession chain preserved
        checks["l0_04"] = len(self.hash_chain_sha256) > 0
        if not checks["l0_04"]:
            violations.append("L0-04: hash_chain_sha256 not initialized")
        
        # L0-05: compliance gate possible
        checks["l0_05"] = bool(self.version_hash)
        if not checks["l0_05"]:
            violations.append("L0-05: version_hash not set")
        
        compliant = len(violations) == 0
        
        # Update compliance status
        self.l0_compliance_status = checks
        
        return {
            "compliant": compliant,
            "checks": checks,
            "violations": violations,
        }
    
    def evolve(self, changes: Dict[str, Any]) -> str:
        """
        Create new version with amendments.
        
        Appends to amendment_history, recalculates version_hash.
        
        Args:
            changes: Dictionary of field changes
            
        Returns:
            str: New version_hash (SHA-256)
        
        Example:
            >>> new_hash = entity.evolve({"name": "New Name", "category": "updated"})
        """
        import hashlib
        
        # Record amendment
        amendment = {
            "timestamp": datetime.utcnow().isoformat(),
            "change_type": "evolution",
            "data": changes,
            "signature_hash": None,  # To be filled by sign_amendment()
        }
        
        # Append to history
        if not isinstance(self.amendment_history, list):
            self.amendment_history = []
        self.amendment_history.append(amendment)
        
        # Recalculate version hash
        change_str = json.dumps(changes, sort_keys=True)
        new_hash = hashlib.sha256(change_str.encode()).hexdigest()
        
        # Update hash chain
        self.hash_chain_sha256.append(new_hash)
        self.version_hash = new_hash
        self.updated_at = datetime.utcnow()
        
        logger.info(
            f"Entity {self.id} evolved to version {new_hash}",
            extra={"entity_id": str(self.id), "version_hash": new_hash}
        )
        
        return new_hash
    
    def sign_amendment(self, private_key_pem: str) -> str:
        """
        Sign latest amendment for non-repudiation.
        
        Args:
            private_key_pem: RSA private key (PEM format)
            
        Returns:
            str: Signature hash (for audit trail)
        
        Example:
            >>> sig = entity.sign_amendment(private_key)
        """
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64
        
        if not self.amendment_history:
            raise ValueError("No amendments to sign")
        
        latest_amendment = self.amendment_history[-1]
        amendment_str = json.dumps(latest_amendment["data"], sort_keys=True)
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
        )
        
        # Sign with RSA-SHA256
        signature = private_key.sign(
            amendment_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Encode and store
        signature_b64 = base64.b64encode(signature).decode()
        self.amendment_history[-1]["signature_hash"] = signature_b64
        
        logger.info(
            f"Amendment signed for entity {self.id}",
            extra={"entity_id": str(self.id), "signature_b64": signature_b64[:20] + "..."}
        )
        
        return signature_b64
    
    def verify_amendment(self, public_key_pem: str, amendment_index: int = -1) -> bool:
        """
        Verify RSA signature on amendment (third-party verifiable).
        
        Args:
            public_key_pem: RSA public key (PEM format)
            amendment_index: Index in amendment history (-1 = latest)
            
        Returns:
            bool: True if signature is valid
        
        Example:
            >>> if entity.verify_amendment(public_key):
            ...     print("Amendment is authentic")
        """
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64
        
        if not self.amendment_history or amendment_index >= len(self.amendment_history):
            return False
        
        amendment = self.amendment_history[amendment_index]
        signature_b64 = amendment.get("signature_hash")
        
        if not signature_b64:
            return False
        
        try:
            signature = base64.b64decode(signature_b64)
            amendment_str = json.dumps(amendment["data"], sort_keys=True)
            
            # Load public key
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            
            # Verify signature
            public_key.verify(
                signature,
                amendment_str.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
    
    def get_hash_chain_integrity(self) -> Dict[str, Any]:
        """
        Validate hash chain integrity (detect tampering).
        
        Returns:
            Dict[str, Any]: {
                "intact": bool,
                "broken_at_index": int or None,
                "details": [...]
            }
        
        Example:
            >>> integrity = entity.get_hash_chain_integrity()
            >>> if not integrity["intact"]:
            ...     raise HashChainBrokenError(integrity["details"])
        """
        import hashlib
        
        if len(self.hash_chain_sha256) == 0:
            return {"intact": True, "broken_at_index": None, "details": []}
        
        details = []
        for i, hash_value in enumerate(self.hash_chain_sha256):
            # Verify each hash exists in amendment history
            if i < len(self.amendment_history):
                amendment = self.amendment_history[i]
                recomputed = hashlib.sha256(
                    json.dumps(amendment["data"], sort_keys=True).encode()
                ).hexdigest()
                
                if recomputed != hash_value:
                    return {
                        "intact": False,
                        "broken_at_index": i,
                        "details": [
                            f"Hash mismatch at index {i}",
                            f"Expected: {recomputed}",
                            f"Found: {hash_value}"
                        ]
                    }
                details.append(f"Index {i}: ✓ valid")
        
        return {"intact": True, "broken_at_index": None, "details": details}
