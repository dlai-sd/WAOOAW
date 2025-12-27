"""
Unit Tests for PR Review Workflow - Story 2.3
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.github.pr_review import PRReviewWorkflow, PRReviewResult
from waooaw.github.helpers import GitHubHelpers


class TestPRReviewWorkflow:
    """Test PR review workflow."""
    
    def test_review_pr_clean(self):
        """Should approve PR with no violations."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "src/feature.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
                "changes": 50
            }
        ]
        
        mock_comment = MagicMock()
        mock_comment.id = 123
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=10, create_issues=False)
        
        assert result.approved is True
        assert len(result.violations) == 0
        assert len(result.escalations) == 0
        assert len(result.comments_posted) == 1
        assert "No violations" in result.summary or "APPROVED" in result.summary
    
    def test_review_pr_large_file(self):
        """Should detect large file violation."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "src/huge.py",
                "status": "added",
                "additions": 1000,
                "deletions": 0,
                "changes": 1000
            }
        ]
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=10, create_issues=False)
        
        assert len(result.violations) == 1
        assert result.violations[0]["violation_type"] == "Large PR"
        assert result.violations[0]["severity"] == "medium"
        assert result.approved is True  # Medium violations don't block
    
    def test_review_pr_readme_change(self):
        """Should flag README changes for vision check."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15
            }
        ]
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=10, create_issues=False, check_vision=True)
        
        assert len(result.violations) == 1
        assert "vision.yaml" in result.violations[0].get("policy_reference", "")
    
    def test_review_pr_escalation_large(self):
        """Should escalate large PR (>20 files)."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        
        # Create 25 files
        files = [
            {
                "filename": f"src/file{i}.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15
            }
            for i in range(25)
        ]
        mock_gh.get_pr_files.return_value = files
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        mock_issue = MagicMock()
        mock_issue.number = 100
        mock_gh.create_issue.return_value = mock_issue
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=10, create_issues=True)
        
        assert len(result.escalations) == 1
        assert len(result.issues_created) == 1
        assert result.approved is False  # Escalated = not approved
    
    def test_review_pr_no_code_files(self):
        """Should skip non-code files."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        mock_gh.get_pr_files.return_value = [
            {
                "filename": "docs/guide.md",
                "status": "added",
                "additions": 100,
                "deletions": 0,
                "changes": 100
            },
            {
                "filename": "assets/logo.png",
                "status": "added",
                "additions": 0,
                "deletions": 0,
                "changes": 0
            }
        ]
        
        mock_comment = MagicMock()
        mock_gh.comment_on_pr.return_value = mock_comment
        
        workflow = PRReviewWorkflow(mock_gh)
        result = workflow.review_pr(pr_number=10, create_issues=False)
        
        assert len(result.violations) == 0  # No code files = no violations
        assert result.approved is True
    
    def test_generate_review_comment(self):
        """Should generate formatted review comment."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        workflow = PRReviewWorkflow(mock_gh)
        
        comment = workflow._generate_review_comment(
            violations=[
                {"severity": "high", "violation_type": "Test"},
                {"severity": "low", "violation_type": "Test"}
            ],
            escalations=[],
            issues_created=[42, 43]
        )
        
        assert "WowVision Prime Review" in comment
        assert "HIGH" in comment
        assert "LOW" in comment
        assert "#42" in comment
        assert "#43" in comment
    
    def test_approval_logic(self):
        """Should correctly determine approval status."""
        mock_gh = MagicMock(spec=GitHubHelpers)
        workflow = PRReviewWorkflow(mock_gh)
        
        # No violations = approve
        assert workflow._should_approve([], []) is True
        
        # Low/medium violations = approve
        assert workflow._should_approve(
            [{"severity": "low"}, {"severity": "medium"}],
            []
        ) is True
        
        # High violation = reject
        assert workflow._should_approve(
            [{"severity": "high"}],
            []
        ) is False
        
        # Critical violation = reject
        assert workflow._should_approve(
            [{"severity": "critical"}],
            []
        ) is False
        
        # Escalated = reject
        assert workflow._should_approve(
            [],
            [{"trigger": "test"}]
        ) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
