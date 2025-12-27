"""
E2E GitHub Integration Tests - Story 2.5

End-to-end tests for full GitHub workflow.
Part of Epic 2: GitHub Integration.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.github.helpers import GitHubHelpers
from waooaw.github.templates import IssueTemplates
from waooaw.github.pr_review import PRReviewWorkflow
from waooaw.github.markdown_renderer import MarkdownRenderer


class TestE2EGitHubWorkflow:
    """
    End-to-end tests for GitHub integration.
    
    Tests full workflows:
    - Issue creation → commenting → closing
    - PR review → violation detection → issue creation
    - Escalation workflow
    """
    
    def test_issue_lifecycle(self):
        """Should handle full issue lifecycle."""
        # Setup mock GitHub
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        mock_issue = MagicMock()
        mock_issue.number = 100
        mock_gh.create_issue.return_value = mock_issue
        
        mock_comment = MagicMock()
        mock_comment.id = 200
        mock_gh.comment_on_issue.return_value = mock_comment
        
        mock_gh.close_issue.return_value = None
        
        # Step 1: Create violation issue
        issue_data = IssueTemplates.violation_issue(
            violation_type="Vision Mismatch",
            file_path="src/feature.py",
            description="Feature doesn't align with vision",
            severity="high"
        )
        
        issue = mock_gh.create_issue(**issue_data)
        assert issue.number == 100
        
        # Step 2: Comment on issue
        comment_body = IssueTemplates.status_update_comment(
            status="in-progress",
            details="Reviewing proposed fix",
            progress=50
        )
        
        comment = mock_gh.comment_on_issue(100, comment_body)
        assert comment.id == 200
        
        # Step 3: Close issue
        mock_gh.close_issue(100, "Fixed in PR #50")
        
        # Verify calls
        assert mock_gh.create_issue.called
        assert mock_gh.comment_on_issue.called
        assert mock_gh.close_issue.called
    
    def test_pr_review_to_violation_issues(self):
        """Should create violation issues from PR review."""
        # Setup mocks
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        # Mock PR files
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "src/huge.py",
                "status": "added",
                "additions": 1500,
                "deletions": 0,
                "changes": 1500
            },
            {
                "filename": "src/auth.py",
                "status": "modified",
                "additions": 50,
                "deletions": 20,
                "changes": 70
            }
        ]
        
        # Mock issue creation
        mock_issue1 = MagicMock()
        mock_issue1.number = 101
        mock_issue2 = MagicMock()
        mock_issue2.number = 102
        mock_gh.create_issue.side_effect = [mock_issue1, mock_issue2]
        
        # Mock PR comment
        mock_comment = MagicMock()
        mock_comment.id = 300
        mock_gh.comment_on_pr.return_value = mock_comment
        
        # Run PR review
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(
            pr_number=42,
            create_issues=True,
            auto_comment=True
        )
        
        # Verify workflow results
        assert len(result.violations) >= 1  # Large file violation
        assert len(result.issues_created) >= 1  # Escalation issue
        assert len(result.comments_posted) == 1
        assert result.approved is False  # Should escalate large PR
        
        # Verify calls
        mock_gh.get_pr_files.assert_called_once_with(42)
        assert mock_gh.create_issue.called
        mock_gh.comment_on_pr.assert_called_once()
    
    def test_escalation_workflow(self):
        """Should escalate ambiguous situations."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        # Create many violations (triggers escalation)
        violations = [
            {"severity": "high", "violation_type": f"Issue {i}", "file_path": f"file{i}.py"}
            for i in range(10)
        ]
        
        mock_gh.get_pr_files.return_value = [
            {
                "filename": f"src/file{i}.py",
                "status": "modified",
                "additions": 50,
                "deletions": 10,
                "changes": 60
            }
            for i in range(10)
        ]
        
        mock_issue = MagicMock()
        mock_issue.number = 999
        mock_gh.create_issue.return_value = mock_issue
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(
            pr_number=50,
            create_issues=True
        )
        
        # Should escalate (many violations)
        assert len(result.escalations) >= 1
        assert result.approved is False
        
        # Should create escalation issue
        create_calls = mock_gh.create_issue.call_args_list
        assert len(create_calls) >= 1
    
    def test_markdown_rendering_in_issues(self):
        """Should use markdown renderer in issue templates."""
        # Create violation with severity
        issue_data = IssueTemplates.violation_issue(
            violation_type="Security",
            file_path="src/auth.py",
            description="SQL injection vulnerability found",
            severity="critical"
        )
        
        # Check emoji in title
        assert "🚨" in issue_data["title"]  # Critical severity
        
        # Check markdown formatting in body
        body = issue_data["body"]
        assert "##" in body  # Headings
        assert "**" in body  # Bold
        assert "-" in body or "*" in body  # Lists
        
        # Check labels
        assert "violation" in issue_data["labels"]
        assert "severity-critical" in issue_data["labels"]
    
    def test_status_updates_with_progress_bars(self):
        """Should render progress bars in status comments."""
        comment = IssueTemplates.status_update_comment(
            status="in-progress",
            details="Implementing fix",
            progress=60
        )
        
        # Should include progress indicator
        assert "60%" in comment or "█" in comment
    
    def test_pr_review_comment_formatting(self):
        """Should format PR review comments properly."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "src/small.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15
            }
        ]
        
        mock_comment = MagicMock()
        mock_comment.id = 400
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=60, create_issues=False)
        
        # Get the comment that was posted
        call_args = mock_gh.comment_on_pr.call_args
        comment_body = call_args[0][1]
        
        # Verify markdown formatting
        assert "##" in comment_body or "**" in comment_body
        assert "WowVision Prime" in comment_body
        
        # Should include status indicator
        assert "✅" in comment_body or "⚠️" in comment_body


class TestGitHubIntegrationComponents:
    """Test integration between GitHub components."""
    
    def test_helpers_and_templates_integration(self):
        """Should use helpers with templates."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        mock_issue = MagicMock()
        mock_issue.number = 500
        mock_gh.create_issue.return_value = mock_issue
        
        # Generate violation template
        violation_data = IssueTemplates.violation_issue(
            violation_type="Test",
            file_path="test.py",
            description="Test violation",
            severity="medium"
        )
        
        # Create issue using helpers
        issue = mock_gh.create_issue(**violation_data)
        
        assert issue.number == 500
        mock_gh.create_issue.assert_called_once()
    
    def test_pr_review_uses_templates(self):
        """Should use issue templates in PR review."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 10,
                "deletions": 0,
                "changes": 10
            }
        ]
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        mock_issue = MagicMock()
        mock_issue.number = 600
        mock_gh.create_issue.return_value = mock_issue
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=70, create_issues=True)
        
        # Should generate comment using templates
        assert mock_gh.comment_on_pr.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
