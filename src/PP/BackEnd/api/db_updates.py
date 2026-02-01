"""DB updates (dev-only) routes.

These endpoints are intentionally guarded:
- disabled in prod-like environments
- require ENABLE_DB_UPDATES
- require an `admin` role token
"""

from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.security import require_admin
from core.config import Settings, get_settings


router = APIRouter(prefix="/db", tags=["db-updates"])


def _plant_admin_db_base_url(app_settings: Settings) -> str:
    base = (app_settings.plant_base_url or "").rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="Plant base URL not configured")
    return f"{base}/api/v1/admin/db"


def _enforce_enabled(app_settings: Settings) -> None:
    if app_settings.is_prod_like or not app_settings.ENABLE_DB_UPDATES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _normalize_single_statement(sql: str) -> str:
    if not sql or not sql.strip():
        raise HTTPException(status_code=400, detail="SQL is required")
    s = sql.strip()
    # Disallow multiple statements as a safety guard.
    # Allow a trailing semicolon.
    if ";" in s[:-1]:
        raise HTTPException(status_code=400, detail="Only a single SQL statement is allowed")
    if s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        raise HTTPException(status_code=400, detail="SQL is required")
    if len(s) > 20_000:
        raise HTTPException(status_code=400, detail="SQL too large")
    return s


class ExecuteSqlRequest(BaseModel):
    sql: str
    confirm: bool = False
    max_rows: int = 100
    statement_timeout_ms: int = 10_000


@router.get("/connection-info")
async def connection_info(
    request: Request,
    _: dict = Depends(require_admin),
    app_settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    _enforce_enabled(app_settings)
    url = f"{_plant_admin_db_base_url(app_settings)}/connection-info"
    headers: Dict[str, str] = {}
    if request.headers.get("Authorization"):
        headers["Authorization"] = request.headers["Authorization"]
    if request.headers.get("X-Correlation-ID"):
        headers["X-Correlation-ID"] = request.headers["X-Correlation-ID"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code >= 400:
        detail: Any = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json()


@router.post("/execute")
async def execute_sql(
    req: ExecuteSqlRequest,
    request: Request,
    _: dict = Depends(require_admin),
    app_settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    _enforce_enabled(app_settings)
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to execute SQL")

    sql = _normalize_single_statement(req.sql)
    max_rows = max(1, min(int(req.max_rows), 500))
    statement_timeout_ms = max(100, min(int(req.statement_timeout_ms), 60_000))

    url = f"{_plant_admin_db_base_url(app_settings)}/execute"
    headers: Dict[str, str] = {}
    if request.headers.get("Authorization"):
        headers["Authorization"] = request.headers["Authorization"]
    if request.headers.get("X-Correlation-ID"):
        headers["X-Correlation-ID"] = request.headers["X-Correlation-ID"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            headers=headers,
            json={
                "sql": sql,
                "confirm": True,
                "max_rows": max_rows,
                "statement_timeout_ms": statement_timeout_ms,
            },
        )

    if resp.status_code >= 400:
        detail: Any = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json()

