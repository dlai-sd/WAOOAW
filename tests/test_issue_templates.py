"""
Unit Tests for Issue Templates - Story 2.2

Tests IssueTemplates class for violation, escalation, approval issues.
"""
import pytest
import json
from datetime import datetime

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.github.templates import IssueTemplates


class TestViolationIssue:
    """Test violation issue template."""
    
    def test_basic_violation(self):
        """Should create basic violation issue."""
        result = IssueTemplates.violation_issue(
            violation_type="Vision Mismatch",
            file_path="src/feature.py",
            description="Feature doesn't align with vision.yaml",
            severity="high"
        )
        
        assert "title" in result
        assert "body" in result
        assert "labels" in result
        assert "🔴" in result["title"]  # High severity emoji
        assert "Vision Mismatch" in result["title"]
        assert "src/feature.py" in result["title"]
        assert "vision.yaml" in result["body"].lower()
        assert "violation" in result["labels"]
        assert "severity-high" in result["labels"]
    
    def test_violation_with_all_fields(self):
        """Should include all optional fields."""
        result = IssueTemplates.violation_issue(
            violation_type="Code Standard",
            file_path="lib/utils.py",
            description="Missing type hints",
            severity="medium",
            policy_reference="CODE_STANDARD.md:L42",
            suggested_fix="Add type hints to all function signatures",
            context={"line": "125-130", "function": "process_data"}
        )
        
        assert "CODE_STANDARD.md:L42" in result["body"]
        assert "Add type hints" in result["body"]
        assert "line" in result["body"]
        assert "process_data" in result["body"]
    
    def test_severity_levels(self):
        """Should handle different severity levels."""
        for severity, emoji in [("low", "🟡"), ("medium", "🟠"), ("high", "🔴"), ("critical", "🚨")]:
            result = IssueTemplates.violation_issue(
                violation_type="Test",
                file_path="test.py",
                description="Test",
                severity=severity
            )
            assert emoji in result["title"]
            assert f"severity-{severity}" in result["labels"]


class TestEscalationIssue:
    """Test escalation issue template."""
    
    def test_basic_escalation(self):
        """Should create basic escalation issue."""
        result = IssueTemplates.escalation_issue(
            trigger="@wowvision-prime",
            reason="Ambiguous requirement needs clarification"
        )
        
        assert "Escalation" in result["title"]
        assert "@wowvision-prime" in result["title"]
        assert "Ambiguous requirement" in result["body"]
        assert "escalation" in result["labels"]
        assert "needs-human-input" in result["labels"]
    
    def test_escalation_with_pr(self):
        """Should include PR reference."""
        result = IssueTemplates.escalation_issue(
            trigger="Ambiguity",
            reason="Multiple interpretations possible",
            pr_number=42,
            files_affected=["src/main.py", "tests/test_main.py"],
            action_required="Please clarify expected behavior"
        )
        
        assert "#42" in result["body"]
        assert "src/main.py" in result["body"]
        assert "tests/test_main.py" in result["body"]
        assert "clarify expected behavior" in result["body"]
    
    def test_escalation_with_context(self):
        """Should include agent context as JSON."""
        context = {
            "current_task": "PR review",
            "decision_pending": "Architecture choice",
            "options": ["Option A", "Option B"]
        }
        
        result = IssueTemplates.escalation_issue(
            trigger="Decision Required",
            reason="Need architectural guidance",
            agent_context=context
        )
        
        assert "Agent Context" in result["body"]
        assert "current_task" in result["body"]
        assert "Architecture choice" in result["body"]


class TestApprovalIssue:
    """Test approval issue template."""
    
    def test_basic_approval(self):
        """Should create basic approval issue."""
        result = IssueTemplates.approval_issue(
            task_completed="Epic 1: Message Bus",
            summary="Implemented Redis Streams message bus with 36 tests passing"
        )
        
        assert "Approval Request" in result["title"]
        assert "Epic 1: Message Bus" in result["title"]
        assert "Redis Streams" in result["body"]
        assert "36 tests" in result["body"]
        assert "approval-request" in result["labels"]
    
    def test_approval_with_metrics(self):
        """Should include metrics."""
        result = IssueTemplates.approval_issue(
            task_completed="Story 2.1",
            summary="GitHub helpers implemented",
            metrics={
                "Tests Passing": "10/10",
                "Coverage": "100%",
                "Lines Added": "320"
            },
            deliverables=[
                "GitHubHelpers class",
                "10 unit tests",
                "Full documentation"
            ]
        )
        
        assert "10/10" in result["body"]
        assert "100%" in result["body"]
        assert "GitHubHelpers class" in result["body"]
        assert "10 unit tests" in result["body"]
    
    def test_approval_with_pr(self):
        """Should reference PR."""
        result = IssueTemplates.approval_issue(
            task_completed="Feature X",
            summary="Complete",
            pr_number=123,
            next_steps="Merge and deploy to staging"
        )
        
        assert "#123" in result["body"]
        assert "staging" in result["body"]


class TestStatusUpdateComment:
    """Test status update comments."""
    
    def test_in_progress_status(self):
        """Should create in-progress status."""
        comment = IssueTemplates.status_update_comment(
            status="in-progress",
            details="Working on GitHub integration",
            progress=60,
            eta="2 hours"
        )
        
        assert "⏳" in comment
        assert "IN-PROGRESS" in comment
        assert "GitHub integration" in comment
        assert "60%" in comment
        assert "2 hours" in comment
        assert "█" in comment  # Progress bar
    
    def test_blocked_status(self):
        """Should show blockers."""
        comment = IssueTemplates.status_update_comment(
            status="blocked",
            details="Waiting for dependency",
            blockers=[
                "Redis not available in test environment",
                "GitHub API rate limit exceeded"
            ]
        )
        
        assert "🚫" in comment
        assert "BLOCKED" in comment
        assert "Redis not available" in comment
        assert "rate limit" in comment
    
    def test_complete_status(self):
        """Should show completion."""
        comment = IssueTemplates.status_update_comment(
            status="complete",
            details="All tests passing, ready for review",
            progress=100
        )
        
        assert "✅" in comment
        assert "COMPLETE" in comment
        assert "100%" in comment
        assert "█" * 20 in comment  # Full progress bar


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
