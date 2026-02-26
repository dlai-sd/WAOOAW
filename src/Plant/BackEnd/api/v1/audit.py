"""
Audit endpoints — constitutional compliance checks + business event log.

Iteration 2 additions:
  POST /audit/events  — write a business event (service key auth)
  GET  /audit/events  — query events (admin JWT required)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.database import get_db, get_db_session
from core.config import get_settings
from core.security import verify_token
from services.audit_service import AuditService
from services.audit_log_service import AuditLogService
from services.policy_denial_audit import PolicyDenialAuditStore, get_policy_denial_audit_store
from schemas.audit_log import AuditEventCreate, AuditEventResponse, AuditEventsListResponse

_settings = get_settings()

router = APIRouter(prefix="/audit", tags=["audit"])


# ---------------------------------------------------------------------------
# E2-S3 helper — service key verification
# ---------------------------------------------------------------------------

def _verify_audit_service_key(request: Request) -> None:
    """FastAPI dependency: verify X-Audit-Service-Key header."""
    provided_key = request.headers.get("X-Audit-Service-Key", "")
    expected_key = _settings.audit_service_key
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AUDIT_KEY_MISSING",
        )
    if provided_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AUDIT_KEY_INVALID",
        )


# ---------------------------------------------------------------------------
# E2-S2 helper — admin JWT check
# ---------------------------------------------------------------------------

def _require_admin_jwt(request: Request) -> Dict[str, Any]:
    """FastAPI dependency: require a valid JWT with admin role."""
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    )
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    claims = verify_token(parts[1])
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return claims


# ---------------------------------------------------------------------------
# E2-S1 — POST /audit/events (service key protected)
# ---------------------------------------------------------------------------

def get_audit_log_service(
    db: AsyncSession = Depends(get_db_session),
) -> AuditLogService:
    return AuditLogService(db)


@router.post(
    "/events",
    response_model=AuditEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Write an audit event (service key required)",
)
async def create_audit_event(
    payload: AuditEventCreate,
    _key: None = Depends(_verify_audit_service_key),
    svc: AuditLogService = Depends(get_audit_log_service),
) -> AuditEventResponse:
    """Write a business event to the audit log.

    Protected by X-Audit-Service-Key header — JWT is NOT required.
    This endpoint is in the Gateway public path list.
    """
    record = await svc.log_event(payload)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write audit event",
        )
    return AuditEventResponse.from_orm_model(record)


# ---------------------------------------------------------------------------
# E2-S2 — GET /audit/events (admin JWT required)
# ---------------------------------------------------------------------------

@router.get(
    "/events",
    response_model=AuditEventsListResponse,
    summary="Query audit events (admin JWT required)",
)
async def list_audit_events(
    user_id: Optional[UUID] = None,
    email: Optional[str] = None,
    screen: Optional[str] = None,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    _claims: Dict[str, Any] = Depends(_require_admin_jwt),
    svc: AuditLogService = Depends(get_audit_log_service),
) -> AuditEventsListResponse:
    """Query business audit events with optional filters.

    Requires a valid JWT with admin role. Soft-deleted records never returned.
    page_size is clamped to a maximum of 100.
    """
    if page_size > 100:
        page_size = 100
    if page < 1:
        page = 1

    items, total = await svc.query_events(
        user_id=user_id,
        email=email,
        screen=screen,
        action=action,
        outcome=outcome,
        from_ts=from_ts,
        to_ts=to_ts,
        page=page,
        page_size=page_size,
    )

    return AuditEventsListResponse(
        items=[AuditEventResponse.from_orm_model(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


# ---------------------------------------------------------------------------
# Existing: constitutional compliance audit endpoints (unchanged)
# ---------------------------------------------------------------------------


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
