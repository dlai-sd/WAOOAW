"""
Unit tests for AuditLogger service
"""

import pytest
from datetime import datetime, timedelta
from waooaw_portal.services.audit_logger import (
    AuditLogger,
    AuditAction,
    AuditLevel,
    AuditLogEntry,
)


@pytest.fixture
def audit_logger():
    """Create audit logger instance"""
    return AuditLogger(retention_days=90, max_entries=1000)


class TestAuditLogger:
    """Test AuditLogger basic functionality"""

    def test_log_simple_event(self, audit_logger):
        """Test logging a simple event"""
        audit_logger.log(
            action=AuditAction.CREATE,
            user="admin",
            resource="agent",
            resource_id="agent-123",
        )

        assert len(audit_logger.logs) == 1
        entry = audit_logger.logs[0]
        assert entry.action == AuditAction.CREATE
        assert entry.user == "admin"
        assert entry.resource == "agent"
        assert entry.resource_id == "agent-123"

    def test_log_with_details(self, audit_logger):
        """Test logging with additional details"""
        details = {"old_value": "stopped", "new_value": "running"}

        audit_logger.log(
            action=AuditAction.UPDATE,
            user="admin",
            resource="agent",
            resource_id="agent-123",
            details=details,
        )

        entry = audit_logger.logs[0]
        assert entry.details == details

    def test_log_with_level(self, audit_logger):
        """Test logging with different levels"""
        audit_logger.log(
            action=AuditAction.DELETE,
            user="admin",
            resource="agent",
            resource_id="agent-123",
            level=AuditLevel.WARNING,
        )

        entry = audit_logger.logs[0]
        assert entry.level == AuditLevel.WARNING

    def test_log_with_error(self, audit_logger):
        """Test logging failed operation"""
        audit_logger.log(
            action=AuditAction.START,
            user="admin",
            resource="agent",
            resource_id="agent-123",
            result="failure",
            error_message="Agent not found",
            level=AuditLevel.ERROR,
        )

        entry = audit_logger.logs[0]
        assert entry.result == "failure"
        assert entry.error_message == "Agent not found"
        assert entry.level == AuditLevel.ERROR

    def test_log_with_metadata(self, audit_logger):
        """Test logging with IP and session"""
        audit_logger.log(
            action=AuditAction.LOGIN,
            user="admin",
            resource="auth",
            resource_id="session-456",
            ip_address="192.168.1.1",
            session_id="sess-789",
        )

        entry = audit_logger.logs[0]
        assert entry.ip_address == "192.168.1.1"
        assert entry.session_id == "sess-789"


class TestAuditQuery:
    """Test audit log querying"""

    def test_query_all(self, audit_logger):
        """Test querying all logs"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.UPDATE, "admin", "agent", "agent-2")
        audit_logger.log(AuditAction.DELETE, "admin", "agent", "agent-3")

        results = audit_logger.query()

        assert len(results) == 3

    def test_query_by_user(self, audit_logger):
        """Test querying by user"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.CREATE, "user1", "agent", "agent-2")
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-3")

        results = audit_logger.query(user="admin")

        assert len(results) == 2
        assert all(e.user == "admin" for e in results)

    def test_query_by_action(self, audit_logger):
        """Test querying by action"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.UPDATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.DELETE, "admin", "agent", "agent-1")

        results = audit_logger.query(action=AuditAction.UPDATE)

        assert len(results) == 1
        assert results[0].action == AuditAction.UPDATE

    def test_query_by_resource(self, audit_logger):
        """Test querying by resource"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.CREATE, "admin", "config", "config-1")
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-2")

        results = audit_logger.query(resource="agent")

        assert len(results) == 2
        assert all(e.resource == "agent" for e in results)

    def test_query_by_level(self, audit_logger):
        """Test querying by level"""
        audit_logger.log(
            AuditAction.CREATE, "admin", "agent", "agent-1", level=AuditLevel.INFO
        )
        audit_logger.log(
            AuditAction.DELETE, "admin", "agent", "agent-2", level=AuditLevel.WARNING
        )
        audit_logger.log(
            AuditAction.UPDATE, "admin", "agent", "agent-3", level=AuditLevel.ERROR
        )

        results = audit_logger.query(level=AuditLevel.ERROR)

        assert len(results) == 1
        assert results[0].level == AuditLevel.ERROR

    def test_query_by_result(self, audit_logger):
        """Test querying by result"""
        audit_logger.log(
            AuditAction.CREATE, "admin", "agent", "agent-1", result="success"
        )
        audit_logger.log(
            AuditAction.CREATE, "admin", "agent", "agent-2", result="failure"
        )
        audit_logger.log(
            AuditAction.CREATE, "admin", "agent", "agent-3", result="success"
        )

        results = audit_logger.query(result="failure")

        assert len(results) == 1
        assert results[0].result == "failure"

    def test_query_with_time_window(self, audit_logger):
        """Test querying with time window"""
        now = datetime.now()

        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")

        # Query recent logs
        start_time = now - timedelta(seconds=10)
        results = audit_logger.query(start_time=start_time)

        assert len(results) >= 1

    def test_query_with_limit(self, audit_logger):
        """Test querying with limit"""
        for i in range(10):
            audit_logger.log(AuditAction.CREATE, "admin", "agent", f"agent-{i}")

        results = audit_logger.query(limit=5)

        assert len(results) == 5

    def test_query_multiple_filters(self, audit_logger):
        """Test querying with multiple filters"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.UPDATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.CREATE, "user1", "agent", "agent-2")

        results = audit_logger.query(user="admin", action=AuditAction.CREATE)

        assert len(results) == 1
        assert results[0].user == "admin"
        assert results[0].action == AuditAction.CREATE


class TestAuditRecent:
    """Test getting recent logs"""

    def test_get_recent_default(self, audit_logger):
        """Test getting recent logs with default count"""
        for i in range(100):
            audit_logger.log(AuditAction.CREATE, "admin", "agent", f"agent-{i}")

        recent = audit_logger.get_recent()

        assert len(recent) == 50

    def test_get_recent_custom_count(self, audit_logger):
        """Test getting recent logs with custom count"""
        for i in range(100):
            audit_logger.log(AuditAction.CREATE, "admin", "agent", f"agent-{i}")

        recent = audit_logger.get_recent(count=10)

        assert len(recent) == 10

    def test_get_recent_order(self, audit_logger):
        """Test that recent logs are in reverse chronological order"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-2")
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-3")

        recent = audit_logger.get_recent(count=3)

        # Newest first
        assert recent[0].resource_id == "agent-3"
        assert recent[1].resource_id == "agent-2"
        assert recent[2].resource_id == "agent-1"


class TestAuditCleanup:
    """Test audit log cleanup"""

    def test_cleanup_old_logs(self, audit_logger):
        """Test cleaning up old logs"""
        audit_logger.retention_days = 0.001  # Very short retention

        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-old")

        import time

        time.sleep(0.1)

        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-new")

        # Cleanup
        audit_logger.cleanup_old_logs()

        assert len(audit_logger.logs) == 1
        assert audit_logger.logs[0].resource_id == "agent-new"

    def test_cleanup_no_old_logs(self, audit_logger):
        """Test cleanup when no old logs"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-2")

        original_count = len(audit_logger.logs)

        audit_logger.cleanup_old_logs()

        assert len(audit_logger.logs) == original_count


class TestAuditStats:
    """Test audit statistics"""

    def test_get_stats(self, audit_logger):
        """Test getting audit logger statistics"""
        audit_logger.log(AuditAction.CREATE, "admin", "agent", "agent-1")
        audit_logger.log(AuditAction.UPDATE, "admin", "agent", "agent-1")
        audit_logger.log(
            AuditAction.DELETE, "admin", "agent", "agent-1", level=AuditLevel.WARNING
        )

        stats = audit_logger.get_stats()

        assert stats["total_entries"] == 3
        assert stats["retention_days"] == 90
        assert stats["max_entries"] == 1000
        assert "action_counts" in stats
        assert stats["action_counts"]["create"] == 1
        assert stats["action_counts"]["update"] == 1
        assert stats["action_counts"]["delete"] == 1
        assert "level_counts" in stats
        assert stats["level_counts"]["info"] == 2
        assert stats["level_counts"]["warning"] == 1


class TestAuditExport:
    """Test audit log export"""

    def test_export_json(self, audit_logger):
        """Test exporting logs as JSON"""
        audit_logger.log(
            AuditAction.CREATE,
            "admin",
            "agent",
            "agent-1",
            details={"type": "sdk"},
        )

        export = audit_logger.export_logs(format="json")

        assert isinstance(export, str)
        assert "agent-1" in export
        assert "admin" in export

    def test_export_unsupported_format(self, audit_logger):
        """Test exporting with unsupported format"""
        with pytest.raises(ValueError):
            audit_logger.export_logs(format="xml")


class TestAuditEdgeCases:
    """Test edge cases"""

    def test_max_entries_limit(self, audit_logger):
        """Test max entries limit"""
        audit_logger.max_entries = 10

        # Add more than max
        for i in range(20):
            audit_logger.log(AuditAction.CREATE, "admin", "agent", f"agent-{i}")

        # Should be trimmed
        assert len(audit_logger.logs) == 10
        # Oldest should be removed
        assert audit_logger.logs[0].resource_id == "agent-10"

    def test_empty_details(self, audit_logger):
        """Test logging with empty details"""
        audit_logger.log(
            AuditAction.CREATE,
            "admin",
            "agent",
            "agent-1",
            details={},
        )

        entry = audit_logger.logs[0]
        assert entry.details == {}

    def test_query_empty_logs(self, audit_logger):
        """Test querying with no logs"""
        results = audit_logger.query()
        assert len(results) == 0

    def test_get_recent_empty(self, audit_logger):
        """Test getting recent with no logs"""
        recent = audit_logger.get_recent()
        assert len(recent) == 0


class TestAuditDataClasses:
    """Test data classes"""

    def test_audit_log_entry_creation(self):
        """Test AuditLogEntry creation"""
        now = datetime.now()
        entry = AuditLogEntry(
            timestamp=now,
            action=AuditAction.CREATE,
            level=AuditLevel.INFO,
            user="admin",
            resource="agent",
            resource_id="agent-1",
            details={"key": "value"},
            result="success",
        )

        assert entry.timestamp == now
        assert entry.action == AuditAction.CREATE
        assert entry.level == AuditLevel.INFO
        assert entry.user == "admin"
        assert entry.resource == "agent"
        assert entry.resource_id == "agent-1"

    def test_audit_log_entry_to_dict(self):
        """Test converting entry to dictionary"""
        now = datetime.now()
        entry = AuditLogEntry(
            timestamp=now,
            action=AuditAction.UPDATE,
            level=AuditLevel.WARNING,
            user="admin",
            resource="config",
            resource_id="config-1",
        )

        d = entry.to_dict()

        assert d["action"] == "update"
        assert d["level"] == "warning"
        assert d["user"] == "admin"
        assert d["resource"] == "config"

    def test_audit_action_enum(self):
        """Test AuditAction enum"""
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.START.value == "start"
        assert AuditAction.STOP.value == "stop"

    def test_audit_level_enum(self):
        """Test AuditLevel enum"""
        assert AuditLevel.INFO.value == "info"
        assert AuditLevel.WARNING.value == "warning"
        assert AuditLevel.ERROR.value == "error"
        assert AuditLevel.CRITICAL.value == "critical"
