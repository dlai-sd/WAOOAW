"""Audit API routes.

PP admin portal routes for constitutional compliance audits.

These handlers must forward the incoming Authorization header to the Plant
Gateway. Otherwise the Plant Gateway will treat calls as unauthenticated.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from api.deps import get_authorization_header
from core.config import settings


router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/run", response_model=Dict[str, Any],
    summary="Run constitutional compliance audit",
    description="""
    Trigger a comprehensive compliance audit via Plant backend.
    
    **Audit Coverage:**
    - L0 Constitutional Rules (governance, uniqueness, capacity, signatures, compliance gates)
    - L1 Constitutional Rules (role-based access, resource limits, API rate limits, certification, versioning)
    - Hash chain integrity validation
    - Entity-specific compliance checks
    
    **Query Parameters:**
    - entity_type: Optional filter (skill/job_role/agent)
    - entity_id: Optional filter (specific entity UUID)
    
    **Returns:**
    - 200 OK: Audit report with compliance score, violations, L0/L1 breakdown
    - 500 Internal Server Error: Audit execution failed
    """)
async def run_compliance_audit(
    request: Request,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (skill/job_role/agent)"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity ID"),
    auth_header: Optional[str] = Depends(get_authorization_header),
):
    """
    Run compliance audit via Plant API.
    
    Query Params:
    - entity_type: skill, job_role, agent (optional)
    - entity_id: UUID (optional)
    """
    try:
        # Build query params
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id
        
        headers: Dict[str, str] = {}
        if auth_header:
            headers["Authorization"] = auth_header
        if request is not None:
            correlation_id = request.headers.get("x-correlation-id")
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id

        # Call Plant audit API (via Plant Gateway)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PLANT_API_URL}/api/v1/audit/run",
                params=params,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            report = response.json()
        
        # TODO: Log audit execution to PP audit trail
        # await audit_service.log_action("audit.compliance_run", None, current_user.id, {
        #     "entity_type": entity_type,
        #     "entity_id": entity_id,
        #     "compliance_score": report.get("compliance_score")
        # })
        
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


@router.get("/tampering/{entity_id}", response_model=Dict[str, Any],
    summary="Detect tampering in entity's audit trail",
    description="""
    Validate hash chain integrity for a specific entity.
    
    **Validation:**
    - Validates audit trail hash chain
    - Detects broken links (tampering evidence)
    - Verifies chronological order
    - Checks signature consistency
    
    **Returns:**
    - 200 OK: Tampering detection report
    - 404 Not Found: Entity doesn't exist
    - 500 Internal Server Error: Detection failed
    """)
async def detect_tampering(
    entity_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
):
    """
    Detect tampering via Plant audit API.
    
    Path Params:
    - entity_id: UUID of entity to check
    """
    try:
        headers: Dict[str, str] = {}
        if auth_header:
            headers["Authorization"] = auth_header
        if request is not None:
            correlation_id = request.headers.get("x-correlation-id")
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id

        # Call Plant audit API (via Plant Gateway)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.PLANT_API_URL}/api/v1/audit/tampering/{entity_id}",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            report = response.json()
        
        # TODO: Log tampering check to PP audit trail
        # await audit_service.log_action("audit.tampering_check", entity_id, current_user.id, {
        #     "tampering_detected": report.get("tampering_detected")
        # })
        
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


@router.get("/export", response_model=Dict[str, Any],
    summary="Export compliance report for external auditors",
    description="""
    Export comprehensive compliance gate report (L0-05 requirement).
    
    **Export Contents:**
    - All L0/L1 compliance checks
    - Entity validation status
    - Hash chain integrity status
    - Signature verification status
    - Timestamp information
    - Exportable JSON format
    
    **Query Parameters:**
    - entity_type: Optional filter (skill/job_role/agent)
    - format: Export format (json/csv) - default json
    
    **Returns:**
    - 200 OK: Compliance report (JSON or CSV)
    - 500 Internal Server Error: Export failed
    """)
async def export_compliance_report(
    request: Request,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (skill/job_role/agent)"),
    format: str = Query("json", description="Export format (json/csv)"),
    auth_header: Optional[str] = Depends(get_authorization_header),
):
    """
    Export compliance report via Plant audit API.
    
    Query Params:
    - entity_type: skill, job_role, agent (optional)
    - format: json, csv (default: json)
    """
    try:
        # Build query params
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
        
        headers: Dict[str, str] = {}
        if auth_header:
            headers["Authorization"] = auth_header
        if request is not None:
            correlation_id = request.headers.get("x-correlation-id")
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id

        # Call Plant audit API (via Plant Gateway)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.PLANT_API_URL}/api/v1/audit/export",
                params=params,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            report = response.json()
        
        # TODO: Log export to PP audit trail
        # await audit_service.log_action("audit.report_exported", None, current_user.id, {
        #     "entity_type": entity_type,
        #     "format": format
        # })
        
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
