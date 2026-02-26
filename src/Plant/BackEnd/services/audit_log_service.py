"""AuditLogService — Iteration 2, E1-S3.

Provides log_event() for writing and query_events() for reading audit records.
Callers never write SQL directly.

Design notes:
- log_event() is fail-safe: exceptions are caught, logged, and None returned.
  Audit must never break the caller.
- query_events() filters deleted_at IS NULL unconditionally.
- Pagination: page/page_size with offset.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog
from schemas.audit_log import AuditEventCreate

logger = logging.getLogger(__name__)


class AuditLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def log_event(self, payload: AuditEventCreate) -> Optional[AuditLog]:
        """Insert a new audit event. Never raises — returns None on DB error."""
        try:
            record = AuditLog(
                user_id=payload.user_id,
                email=payload.email,
                ip_address=payload.ip_address,
                user_agent=payload.user_agent,
                screen=payload.screen,
                action=payload.action,
                outcome=payload.outcome,
                detail=payload.detail,
                metadata_json=payload.metadata or {},
                correlation_id=payload.correlation_id,
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "audit_log: failed to write event screen=%s action=%s",
                payload.screen,
                payload.action,
                exc_info=True,
            )
            await self.db.rollback()
            return None

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def query_events(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        email: Optional[str] = None,
        screen: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """Return paginated non-deleted audit events matching the given filters.

        Returns (items, total_count).
        """
        base_stmt = select(AuditLog).where(AuditLog.deleted_at.is_(None))

        if user_id is not None:
            base_stmt = base_stmt.where(AuditLog.user_id == user_id)
        if email is not None:
            base_stmt = base_stmt.where(AuditLog.email == email)
        if screen is not None:
            base_stmt = base_stmt.where(AuditLog.screen == screen)
        if action is not None:
            base_stmt = base_stmt.where(AuditLog.action == action)
        if outcome is not None:
            base_stmt = base_stmt.where(AuditLog.outcome == outcome)
        if from_ts is not None:
            base_stmt = base_stmt.where(AuditLog.timestamp >= from_ts)
        if to_ts is not None:
            base_stmt = base_stmt.where(AuditLog.timestamp <= to_ts)

        # Total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total: int = total_result.scalar_one()

        # Paginated results — newest first
        offset = (page - 1) * page_size
        paged_stmt = (
            base_stmt
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(paged_stmt)
        items = list(result.scalars().all())

        return items, total
