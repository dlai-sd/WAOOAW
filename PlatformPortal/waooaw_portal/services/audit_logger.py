"""
Audit Logger Service

Records and manages audit logs for all platform operations.
Provides audit trail querying, filtering, and compliance reporting.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Audit action types"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    MODIFY_CONFIG = "modify_config"


class AuditLevel(Enum):
    """Audit log severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """Single audit log entry"""

    timestamp: datetime
    action: AuditAction
    level: AuditLevel
    user: str
    resource: str
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    result: str = "success"
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/export"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "level": self.level.value,
            "user": self.user,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "details": self.details,
            "result": self.result,
            "error_message": self.error_message,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
        }


class AuditLogger:
    """
    Audit logging service for compliance and security.

    Features:
    - Comprehensive audit trail
    - Structured logging
    - Queryable audit history
    - Compliance reporting
    - Automatic retention management
    """

    def __init__(self, retention_days: int = 90, max_entries: int = 100000):
        """
        Initialize audit logger.

        Args:
            retention_days: Days to retain audit logs
            max_entries: Maximum log entries to keep in memory
        """
        self.logs: List[AuditLogEntry] = []
        self.retention_days = retention_days
        self.max_entries = max_entries

    def log(
        self,
        action: AuditAction,
        user: str,
        resource: str,
        resource_id: str,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        result: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Log an audit event.

        Args:
            action: Action performed
            user: User who performed action
            resource: Resource type
            resource_id: Resource identifier
            level: Log level
            details: Additional details
            result: Operation result
            error_message: Error message if failed
            ip_address: Client IP address
            session_id: Session identifier
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            action=action,
            level=level,
            user=user,
            resource=resource,
            resource_id=resource_id,
            details=details or {},
            result=result,
            error_message=error_message,
            ip_address=ip_address,
            session_id=session_id,
        )

        self.logs.append(entry)

        # Trim if exceeds max
        if len(self.logs) > self.max_entries:
            self.logs = self.logs[-self.max_entries :]

        logger.info(
            f"Audit log: {user} {action.value} {resource}:{resource_id} -> {result}"
        )

    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        result: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """
        Query audit logs with filters.

        Args:
            start_time: Start time filter
            end_time: End time filter
            user: User filter
            action: Action filter
            resource: Resource filter
            level: Level filter
            result: Result filter (success/failure)
            limit: Maximum results

        Returns:
            Filtered audit log entries
        """
        results = self.logs

        # Apply filters
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        if user:
            results = [e for e in results if e.user == user]
        if action:
            results = [e for e in results if e.action == action]
        if resource:
            results = [e for e in results if e.resource == resource]
        if level:
            results = [e for e in results if e.level == level]
        if result:
            results = [e for e in results if e.result == result]

        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)

        return results[:limit]

    def get_recent(self, count: int = 50) -> List[AuditLogEntry]:
        """Get most recent audit logs"""
        return sorted(self.logs, key=lambda e: e.timestamp, reverse=True)[:count]

    def cleanup_old_logs(self):
        """Remove logs older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        original_count = len(self.logs)
        self.logs = [e for e in self.logs if e.timestamp > cutoff]
        removed = original_count - len(self.logs)
        logger.info(f"Cleaned up {removed} old audit log entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logger statistics"""
        action_counts = {}
        level_counts = {}

        for entry in self.logs:
            action_counts[entry.action.value] = (
                action_counts.get(entry.action.value, 0) + 1
            )
            level_counts[entry.level.value] = level_counts.get(entry.level.value, 0) + 1

        return {
            "total_entries": len(self.logs),
            "retention_days": self.retention_days,
            "max_entries": self.max_entries,
            "action_counts": action_counts,
            "level_counts": level_counts,
            "oldest_entry": (self.logs[0].timestamp.isoformat() if self.logs else None),
            "newest_entry": (
                self.logs[-1].timestamp.isoformat() if self.logs else None
            ),
        }

    def export_logs(self, format: str = "json") -> str:
        """
        Export audit logs.

        Args:
            format: Export format (json, csv)

        Returns:
            Exported logs as string
        """
        if format == "json":
            return json.dumps([e.to_dict() for e in self.logs], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
