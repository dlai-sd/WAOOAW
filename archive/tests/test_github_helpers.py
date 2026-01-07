"""
Unit Tests for GitHub Helpers - Story 2.1

Tests GitHubHelpers class with mocked PyGithub.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from github import GithubException

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.github.helpers import GitHubHelpers


class TestGitHubHelpers:
    """Test GitHub helper functions."""
    
    @patch("waooaw.github.helpers.Github")
    def test_init(self, mock_github_class):
        """Should initialize with token and repo name."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.name = "WAOOAW"
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        helpers = GitHubHelpers(
            github_token="test_token",
            repo_name="dlai-sd/WAOOAW"
        )
        
        assert helpers.repo_name == "dlai-sd/WAOOAW"
        assert helpers.repo == mock_repo
        mock_github_class.assert_called_once_with("test_token")
        mock_github.get_repo.assert_called_once_with("dlai-sd/WAOOAW")
    
    @patch("waooaw.github.helpers.Github")
    def test_create_issue(self, mock_github_class):
        """Should create issue with title, body, labels."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_repo.create_issue.return_value = mock_issue
        
        issue = helpers.create_issue(
            title="Test Issue",
            body="Issue body",
            labels=["bug", "enhancement"],
            assignees=["developer"]
        )
        
        assert issue.number == 42
        mock_repo.create_issue.assert_called_once_with(
            title="Test Issue",
            body="Issue body",
            labels=["bug", "enhancement"],
            assignees=["developer"]
        )
    
    @patch("waooaw.github.helpers.Github")
    def test_comment_on_issue(self, mock_github_class):
        """Should add comment to existing issue."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_issue = MagicMock()
        mock_comment = MagicMock()
        mock_comment.id = 123
        mock_issue.create_comment.return_value = mock_comment
        mock_repo.get_issue.return_value = mock_issue
        
        comment = helpers.comment_on_issue(42, "Great work!")
        
        assert comment.id == 123
        mock_repo.get_issue.assert_called_once_with(42)
        mock_issue.create_comment.assert_called_once_with("Great work!")
    
    @patch("waooaw.github.helpers.Github")
    def test_comment_on_pr(self, mock_github_class):
        """Should add comment to PR (using issue API)."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_issue = MagicMock()
        mock_comment = MagicMock()
        mock_issue.create_comment.return_value = mock_comment
        mock_repo.get_issue.return_value = mock_issue
        
        comment = helpers.comment_on_pr(10, "LGTM!")
        
        mock_repo.get_issue.assert_called_once_with(10)
        mock_issue.create_comment.assert_called_once_with("LGTM!")
    
    @patch("waooaw.github.helpers.Github")
    def test_get_pr_files(self, mock_github_class):
        """Should retrieve files changed in PR."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        # Mock PR with 2 files
        mock_pr = MagicMock()
        mock_file1 = MagicMock()
        mock_file1.filename = "src/main.py"
        mock_file1.status = "modified"
        mock_file1.additions = 10
        mock_file1.deletions = 5
        mock_file1.changes = 15
        mock_file1.patch = "@@ -1,5 +1,10 @@"
        
        mock_file2 = MagicMock()
        mock_file2.filename = "tests/test_new.py"
        mock_file2.status = "added"
        mock_file2.additions = 50
        mock_file2.deletions = 0
        mock_file2.changes = 50
        mock_file2.patch = "@@ -0,0 +1,50 @@"
        
        mock_pr.get_files.return_value = [mock_file1, mock_file2]
        mock_repo.get_pull.return_value = mock_pr
        
        files = helpers.get_pr_files(10)
        
        assert len(files) == 2
        assert files[0]["filename"] == "src/main.py"
        assert files[0]["status"] == "modified"
        assert files[0]["additions"] == 10
        assert files[1]["filename"] == "tests/test_new.py"
        assert files[1]["status"] == "added"
    
    @patch("waooaw.github.helpers.Github")
    def test_get_file_content(self, mock_github_class):
        """Should retrieve file content from repo."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_content = MagicMock()
        mock_content.decoded_content = b"# README\n\nHello World!"
        mock_repo.get_contents.return_value = mock_content
        
        content = helpers.get_file_content("README.md", ref="main")
        
        assert content == "# README\n\nHello World!"
        mock_repo.get_contents.assert_called_once_with("README.md", ref="main")
    
    @patch("waooaw.github.helpers.Github")
    def test_list_open_prs(self, mock_github_class):
        """Should list open PRs."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_pr1 = MagicMock()
        mock_pr1.number = 10
        mock_pr2 = MagicMock()
        mock_pr2.number = 11
        
        mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
        
        prs = helpers.list_open_prs(limit=10)
        
        assert len(prs) == 2
        assert prs[0].number == 10
        assert prs[1].number == 11
        mock_repo.get_pulls.assert_called_once_with(
            state="open",
            sort="created",
            direction="desc"
        )
    
    @patch("waooaw.github.helpers.Github")
    def test_add_labels_to_issue(self, mock_github_class):
        """Should add labels to issue."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        
        helpers.add_labels_to_issue(42, ["bug", "priority-high"])
        
        mock_repo.get_issue.assert_called_once_with(42)
        mock_issue.add_to_labels.assert_called_once_with("bug", "priority-high")
    
    @patch("waooaw.github.helpers.Github")
    def test_close_issue(self, mock_github_class):
        """Should close issue with optional comment."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        
        helpers.close_issue(42, comment="Fixed in #43")
        
        mock_repo.get_issue.assert_called_once_with(42)
        mock_issue.create_comment.assert_called_once_with("Fixed in #43")
        mock_issue.edit.assert_called_once_with(state="closed")
    
    @patch("waooaw.github.helpers.Github")
    def test_error_handling(self, mock_github_class):
        """Should propagate GithubException errors."""
        mock_github, mock_repo, helpers = self._setup_mocks(mock_github_class)
        
        mock_repo.create_issue.side_effect = GithubException(
            status=404,
            data={"message": "Not Found"},
            headers={}
        )
        
        with pytest.raises(GithubException):
            helpers.create_issue("Test", "Body")
    
    def _setup_mocks(self, mock_github_class):
        """Helper to setup common mocks."""
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.name = "WAOOAW"
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        helpers = GitHubHelpers("test_token", "dlai-sd/WAOOAW")
        return mock_github, mock_repo, helpers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
