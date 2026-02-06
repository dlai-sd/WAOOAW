"""
Audit endpoints - compliance checks + tampering detection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID

from core.database import get_db
from services.audit_service import AuditService
from services.policy_denial_audit import PolicyDenialAuditStore, get_policy_denial_audit_store


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/policy-denials", response_model=Dict[str, Any])
async def list_policy_denials(
    correlation_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
    store: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
):
    records = store.list_records(
        correlation_id=correlation_id,
        customer_id=customer_id,
        agent_id=agent_id,
        limit=limit,
    )
    return {
        "count": len(records),
        "records": [r.model_dump(mode="json") for r in records],
    }


@router.post("/run", response_model=Dict[str, Any])
async def run_compliance_audit(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Run constitutional compliance audit.
    
    - Validates all entities (or filtered by type/ID)
    - Checks L0/L1 compliance
    - Validates hash chain integrity
    - Returns audit report
    """
    try:
        service = AuditService(db)
        report = await service.run_compliance_audit(
            entity_type=entity_type,
            entity_id=entity_id
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/tampering/{entity_id}", response_model=Dict[str, Any])
async def detect_tampering(
    entity_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Detect tampering in entity's audit trail.
    
    - Validates hash chain integrity
    - Detects broken links
    - Returns tampering detection report
    """
    service = AuditService(db)
    report = await service.detect_tampering(entity_id)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return report


@router.get("/export", response_model=Dict[str, Any])
async def export_compliance_report(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export compliance gate report for external auditors.
    
    This implements L0-05: Compliance gate must be exportable.
    
    - Includes all L0/L1 checks
    - Includes signature verification status
    - Returns JSON report
    """
    try:
        service = AuditService(db)
        report = await service.export_compliance_report(entity_type=entity_type)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
