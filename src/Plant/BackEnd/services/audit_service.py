"""
Audit service - L0/L1 compliance checks + hash chain validation
"""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from models.base_entity import BaseEntity
from models.skill import Skill
from models.job_role import JobRole
from models.agent import Agent
from validators.constitutional_validator import validate_constitutional_alignment
from security.hash_chain import validate_chain


class AuditService:
    """Service for constitutional compliance audits."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def run_compliance_audit(
        self,
        entity_type: str = None,
        entity_id: UUID = None,
    ) -> Dict[str, Any]:
        """
        Run constitutional compliance audit on entities.
        
        Args:
            entity_type: Filter by type (Skill/JobRole/Agent/Team/Industry)
            entity_id: Audit single entity by ID
        
        Returns:
            Audit report with violations, warnings, and statistics
        """
        entities = []
        
        if entity_id:
            # Audit single entity
            entity = self.db.query(BaseEntity).filter(BaseEntity.id == entity_id).first()
            if entity:
                entities = [entity]
        elif entity_type:
            # Audit by type
            entities = self.db.query(BaseEntity).filter(
                BaseEntity.entity_type == entity_type,
                BaseEntity.status == "active"
            ).all()
        else:
            # Audit all entities
            entities = self.db.query(BaseEntity).filter(
                BaseEntity.status == "active"
            ).all()
        
        # Run checks
        results = {
            "total_entities": len(entities),
            "compliant": 0,
            "violations": [],
            "warnings": [],
            "statistics": {
                "l0_pass": 0,
                "l1_pass": 0,
                "hash_chain_intact": 0,
            }
        }
        
        for entity in entities:
            # L0/L1 checks
            validation_result = validate_constitutional_alignment(entity)
            
            if validation_result["compliant"]:
                results["compliant"] += 1
                results["statistics"]["l0_pass"] += 1
                if validation_result.get("l1_checks_passed"):
                    results["statistics"]["l1_pass"] += 1
            else:
                results["violations"].append({
                    "entity_id": str(entity.id),
                    "entity_type": entity.entity_type,
                    "violations": validation_result["violations"]
                })
            
            # Hash chain integrity
            integrity_result = entity.get_hash_chain_integrity()
            if integrity_result["intact"]:
                results["statistics"]["hash_chain_intact"] += 1
            else:
                results["violations"].append({
                    "entity_id": str(entity.id),
                    "entity_type": entity.entity_type,
                    "violation": "Hash chain broken",
                    "details": integrity_result
                })
        
        return results
    
    async def detect_tampering(self, entity_id: UUID) -> Dict[str, Any]:
        """
        Detect tampering in entity's audit trail.
        
        Args:
            entity_id: Entity UUID
        
        Returns:
            Tampering detection report
        """
        entity = self.db.query(BaseEntity).filter(BaseEntity.id == entity_id).first()
        
        if not entity:
            return {"error": f"Entity {entity_id} not found"}
        
        integrity_result = entity.get_hash_chain_integrity()
        
        return {
            "entity_id": str(entity.id),
            "entity_type": entity.entity_type,
            "tampered": not integrity_result["intact"],
            "broken_at_index": integrity_result.get("broken_at_index"),
            "details": integrity_result.get("details", {}),
            "amendment_count": len(entity.amendment_history),
            "hash_chain_length": len(entity.hash_chain_sha256),
        }
    
    async def export_compliance_report(
        self,
        entity_type: str = None
    ) -> Dict[str, Any]:
        """
        Export compliance gate report for external auditors.
        
        This implements L0-05: Compliance gate must be exportable.
        
        Args:
            entity_type: Filter by entity type
        
        Returns:
            Compliance report with all L0/L1 checks and signatures
        """
        audit_result = await self.run_compliance_audit(entity_type=entity_type)
        
        # Add signature verification status
        entities = self.db.query(BaseEntity)
        if entity_type:
            entities = entities.filter(BaseEntity.entity_type == entity_type)
        
        entities = entities.filter(BaseEntity.status == "active").all()
        
        signature_status = []
        for entity in entities:
            if entity.amendment_history:
                last_amendment = entity.amendment_history[-1]
                signature_status.append({
                    "entity_id": str(entity.id),
                    "has_signature": "signature" in last_amendment,
                    "signature_verified": False,  # Requires public key verification
                })
        
        return {
            **audit_result,
            "export_timestamp": "now",
            "signature_status": signature_status,
            "exportable": True,
            "format": "JSON",
        }
