"""Admin DB Updates (dev-only).

This is a stop-gap administrative endpoint intended for development/Codespaces only.
It is designed to be called through Plant Gateway.

Security layers:
- Feature flag: ENABLE_DB_UPDATES
- Environment gating: non-prod only
- Requires a Bearer JWT with an `admin` role
- Requires request to be routed via Plant Gateway (X-Gateway header)
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db_session
from core.security import verify_token


router = APIRouter(prefix="/admin/db", tags=["admin-db"])


def _redact_database_url(url: str) -> str:
    if not url:
        return ""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds_and_host = rest.split("@", 1)
    if len(creds_and_host) != 2:
        return url
    creds, host = creds_and_host
    if ":" not in creds:
        return url
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host}"


def _is_prod_like(env: str) -> bool:
    e = (env or "").lower()
    return e in {"prod", "production", "uat", "demo"}


def _enforce_enabled() -> None:
    if _is_prod_like(settings.environment) or not settings.enable_db_updates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _require_admin_via_gateway(request: Request) -> Dict[str, Any]:
    _enforce_enabled()

    if request.headers.get("X-Gateway") != "plant-gateway":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DB updates must be routed via Plant Gateway",
        )

    auth = request.headers.get("Authorization") or ""
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    claims = verify_token(parts[1])
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return claims


def _normalize_single_statement(sql: str) -> str:
    if not sql or not sql.strip():
        raise HTTPException(status_code=400, detail="SQL is required")
    s = sql.strip()
    if ";" in s[:-1]:
        raise HTTPException(status_code=400, detail="Only a single SQL statement is allowed")
    if s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        raise HTTPException(status_code=400, detail="SQL is required")
    if len(s) > settings.db_updates_max_sql_length:
        raise HTTPException(status_code=400, detail="SQL too large")
    return s


class ExecuteSqlRequest(BaseModel):
    sql: str
    confirm: bool = False
    max_rows: int = 100
    statement_timeout_ms: int | None = None


@router.get("/connection-info")
async def connection_info(
    request: Request,
    _: Dict[str, Any] = Depends(_require_admin_via_gateway),
) -> Dict[str, Any]:
    _ = request
    return {
        "environment": settings.environment,
        "database_url": _redact_database_url(settings.database_url),
    }


@router.post("/execute")
async def execute_sql(
    req: ExecuteSqlRequest,
    request: Request,
    _: Dict[str, Any] = Depends(_require_admin_via_gateway),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    _ = request
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to execute SQL")

    sql = _normalize_single_statement(req.sql)
    max_rows = max(1, min(int(req.max_rows), settings.db_updates_max_rows))
    statement_timeout_ms = int(req.statement_timeout_ms or settings.db_updates_statement_timeout_ms)
    statement_timeout_ms = max(100, min(statement_timeout_ms, settings.db_updates_max_statement_timeout_ms))

    try:
        async with session.begin():
            await session.execute(text(f"SET LOCAL statement_timeout TO {statement_timeout_ms}"))
            result = await session.execute(text(sql))

            if result.returns_rows:
                columns = list(result.keys())
                rows = result.fetchmany(max_rows + 1)
                truncated = len(rows) > max_rows
                if truncated:
                    rows = rows[:max_rows]
                return {
                    "type": "select",
                    "columns": columns,
                    "rows": [list(r) for r in rows],
                    "row_count": len(rows),
                    "truncated": truncated,
                }

            return {
                "type": "command",
                "row_count": result.rowcount,
            }
    except ProgrammingError as exc:
        # Typical case: querying a non-existent table (e.g. `SELECT * FROM agents`).
        msg = str(getattr(exc, "orig", None) or exc)
        hint: str | None = None
        if "does not exist" in msg and "relation" in msg:
            hint = (
                "The Plant DB schema uses *_entity table names (e.g. `agent_entity`). "
                "Try: SELECT * FROM agent_entity LIMIT 50"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "sql_error", "message": msg, **({"hint": hint} if hint else {})},
        )
    except DBAPIError as exc:
        msg = str(getattr(exc, "orig", None) or exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "db_error", "message": msg},
        )
