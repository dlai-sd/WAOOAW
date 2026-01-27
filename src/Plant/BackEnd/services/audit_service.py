"""
Audit service - L0/L1 compliance checks + hash chain validation
"""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.base_entity import BaseEntity
from models.skill import Skill
from models.job_role import JobRole
from models.agent import Agent
from validators.constitutional_validator import validate_constitutional_alignment
from security.hash_chain import validate_chain


class AuditService:
    """Service for constitutional compliance audits."""
    
    def __init__(self, db: AsyncSession):
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
            stmt = select(BaseEntity).where(BaseEntity.id == entity_id)
            result = await self.db.execute(stmt)
            entity = result.scalars().first()
            if entity:
                entities = [entity]
        elif entity_type:
            # Audit by type
            stmt = select(BaseEntity).where(
                BaseEntity.entity_type == entity_type,
                BaseEntity.status == "active"
            )
            result = await self.db.execute(stmt)
            entities = result.scalars().all()
        else:
            # Audit all entities
            stmt = select(BaseEntity).where(BaseEntity.status == "active")
            result = await self.db.execute(stmt)
            entities = result.scalars().all()
        
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
        stmt = select(BaseEntity).where(BaseEntity.id == entity_id)
        result = await self.db.execute(stmt)
        entity = result.scalars().first()
        
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
        stmt = select(BaseEntity).where(BaseEntity.status == "active")
        if entity_type:
            stmt = stmt.where(BaseEntity.entity_type == entity_type)
        
        result = await self.db.execute(stmt)
        entities = result.scalars().all()
        
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
from fastapi import HTTPException, Query, Security
from core.auth import User
from services import audit_service
from typing import Optional, Dict, Any
import httpx
from core.config import settings
from fastapi import Response
from datetime import datetime
from core.auth import get_current_user
from clients.plant_api_client import PlantAPIClient  # Adjust the import based on your project structure

async def run_compliance_audit(
    plant_client: PlantAPIClient,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (skill/job_role/agent)"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity ID"),
    current_user: User = Security(get_current_user),
):
    try:
        # Build query params
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id
        
        # Call Plant audit API
        response = await plant_client._request(
            method="POST",
            path="/api/v1/audit/run",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        report = response.json()
        
        await audit_service.log_action("audit.compliance_run", None, current_user.id, {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "compliance_score": report.get("compliance_score")
        })
        
        return report
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Plant audit API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Plant API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {str(e)}")
async def detect_tampering(
    entity_id: str,
    plant_client: PlantAPIClient,
    current_user: User = Security(get_current_user),
):
    try:
        # Call Plant audit API
        response = await plant_client._request(
            method="GET",
            path=f"/api/v1/audit/tampering/{entity_id}",
            timeout=30.0
        )
        response.raise_for_status()
        report = response.json()
        
        await audit_service.log_action("audit.tampering_check", entity_id, current_user.id, {
            "tampering_detected": report.get("tampering_detected")
        })
        
        return report
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Entity not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Plant audit API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Plant API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tampering detection failed: {str(e)}")
async def export_compliance_report(
    plant_client: PlantAPIClient,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (skill/job_role/agent)"),
    format: str = Query("json", description="Export format (json/csv)"),
    current_user: User = Security(get_current_user),
):
    try:
        # Build query params
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
        
        # Call Plant audit API
        response = await plant_client._request(
            method="GET",
            path="/api/v1/audit/export",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        report = response.json()
        
        await audit_service.log_action("audit.report_exported", None, current_user.id, {
            "entity_type": entity_type,
            "format": format
        })
        
        # Convert to CSV if requested
        if format.lower() == "csv":
            csv_content = convert_report_to_csv(report)
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=compliance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
        return report
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Plant audit API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Plant API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
def convert_report_to_csv(report: Dict[str, Any]) -> str:
    """
    Convert JSON compliance report to CSV format.
    
    NOTE: This is a simplified CSV conversion.
    A production implementation would use pandas or csv module.
    """
    lines = []
    
    # Header
    lines.append("Audit Report,Value")
    
    # Summary
    lines.append(f"Compliance Score,{report.get('compliance_score', 'N/A')}")
    lines.append(f"Total Entities,{report.get('total_entities', 0)}")
    lines.append(f"Total Violations,{report.get('total_violations', 0)}")
    lines.append(f"Timestamp,{report.get('timestamp', '')}")
    
    # L0 Breakdown
    lines.append("")
    lines.append("L0 Constitutional Rules")
    l0 = report.get("l0_breakdown", {})
    for rule_name, rule_data in l0.items():
        violations = rule_data.get("violations", 0)
        status = "PASS" if violations == 0 else "FAIL"
        lines.append(f"{rule_name},{status},{violations}")
    
    # L1 Breakdown
    lines.append("")
    lines.append("L1 Constitutional Rules")
    l1 = report.get("l1_breakdown", {})
    for rule_name, rule_data in l1.items():
        violations = rule_data.get("violations", 0)
        status = "PASS" if violations == 0 else "FAIL"
        lines.append(f"{rule_name},{status},{violations}")
    
    return "\n".join(lines)
