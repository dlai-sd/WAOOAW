"""
Unit tests for GitHub API Client (Story 2.1)

Tests all GitHub client methods with mocked responses:
- Issue operations (create, get, comment)
- PR operations (comment, get, list)
- Commit operations (get recent)
- Repository operations (get file content)
- Error handling and retry logic
- Rate limit handling

Uses unittest.mock to avoid real GitHub API calls.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from github import GithubException, RateLimitExceededException

from waooaw.integrations.github_client import (
    GitHubClient,
    get_default_client,
    retry_on_github_error
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_github():
    """Mock PyGithub Github instance"""
    with patch("waooaw.integrations.github_client.Github") as mock:
        yield mock


@pytest.fixture
def mock_repo():
    """Mock GitHub repository"""
    repo = MagicMock()
    repo.full_name = "dlai-sd/WAOOAW"
    repo.default_branch = "main"
    return repo


@pytest.fixture
def github_client(mock_github, mock_repo):
    """GitHubClient with mocked dependencies"""
    mock_github_instance = mock_github.return_value
    mock_github_instance.get_repo.return_value = mock_repo
    
    client = GitHubClient(token="test_token", repo="dlai-sd/WAOOAW")
    return client


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================

def test_client_initialization_with_token_and_repo(mock_github, mock_repo):
    """Test client initializes with explicit token and repo"""
    mock_github_instance = mock_github.return_value
    mock_github_instance.get_repo.return_value = mock_repo
    
    client = GitHubClient(token="test_token", repo="dlai-sd/WAOOAW")
    
    assert client.token == "test_token"
    assert client.repo_name == "dlai-sd/WAOOAW"
    assert client.repo == mock_repo
    mock_github.assert_called_once_with("test_token", per_page=100)


def test_client_initialization_from_env_vars(mock_github, mock_repo, monkeypatch):
    """Test client initializes from environment variables"""
    monkeypatch.setenv("GITHUB_TOKEN", "env_token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    
    mock_github_instance = mock_github.return_value
    mock_github_instance.get_repo.return_value = mock_repo
    
    client = GitHubClient()
    
    assert client.token == "env_token"
    assert client.repo_name == "owner/repo"


def test_client_initialization_missing_token(monkeypatch):
    """Test client raises error if token missing"""
    # Clear env vars
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    
    with pytest.raises(ValueError, match="GitHub token required"):
        GitHubClient(repo="dlai-sd/WAOOAW")


def test_client_initialization_missing_repo(monkeypatch, mock_github, mock_repo):
    """Test client raises error if repo missing"""
    # Clear env vars
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    
    with pytest.raises(ValueError, match="Repository required"):
        GitHubClient(token="test_token")


# ============================================================================
# TEST: CREATE ISSUE
# ============================================================================

def test_create_issue_success(github_client, mock_repo):
    """Test creating issue successfully"""
    mock_issue = MagicMock()
    mock_issue.number = 42
    mock_issue.title = "Test Issue"
    mock_repo.create_issue.return_value = mock_issue
    
    issue = github_client.create_issue(
        title="Test Issue",
        body="Test body",
        labels=["bug", "priority-high"],
        assignee="dlai-sd"
    )
    
    assert issue.number == 42
    mock_repo.create_issue.assert_called_once_with(
        title="Test Issue",
        body="Test body",
        labels=["bug", "priority-high"],
        assignee="dlai-sd"
    )


def test_create_issue_without_optional_params(github_client, mock_repo):
    """Test creating issue without labels/assignee"""
    mock_issue = MagicMock()
    mock_issue.number = 43
    mock_repo.create_issue.return_value = mock_issue
    
    issue = github_client.create_issue(
        title="Simple Issue",
        body="Simple body"
    )
    
    assert issue.number == 43
    mock_repo.create_issue.assert_called_once_with(
        title="Simple Issue",
        body="Simple body",
        labels=[],
        assignee=None
    )


def test_create_issue_github_exception(github_client, mock_repo):
    """Test create issue handles GitHub exceptions"""
    mock_repo.create_issue.side_effect = GithubException(
        status=422,
        data={"message": "Validation failed"},
        headers={}
    )
    
    with pytest.raises(GithubException):
        github_client.create_issue("Test", "Body")


# ============================================================================
# TEST: COMMENT ON PR
# ============================================================================

def test_comment_on_pr_success(github_client, mock_repo):
    """Test commenting on PR successfully"""
    mock_pr = MagicMock()
    mock_repo.get_pull.return_value = mock_pr
    
    github_client.comment_on_pr(
        pr_number=42,
        comment="✅ Vision compliant"
    )
    
    mock_repo.get_pull.assert_called_once_with(42)
    mock_pr.create_issue_comment.assert_called_once_with("✅ Vision compliant")


def test_comment_on_pr_not_found(github_client, mock_repo):
    """Test commenting on non-existent PR"""
    mock_repo.get_pull.side_effect = GithubException(
        status=404,
        data={"message": "Not Found"},
        headers={}
    )
    
    with pytest.raises(GithubException):
        github_client.comment_on_pr(pr_number=999, comment="Test")


# ============================================================================
# TEST: GET OPEN PRS
# ============================================================================

def test_get_open_prs_all(github_client, mock_repo):
    """Test getting all open PRs"""
    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.user.login = "author1"
    mock_pr1.base.ref = "main"
    mock_pr1.labels = []
    
    mock_pr2 = MagicMock()
    mock_pr2.number = 2
    mock_pr2.user.login = "author2"
    mock_pr2.base.ref = "develop"
    mock_pr2.labels = []
    
    mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
    
    prs = github_client.get_open_prs()
    
    assert len(prs) == 2
    mock_repo.get_pulls.assert_called_once_with(
        state="open",
        sort="created",
        direction="desc"
    )


def test_get_open_prs_filtered_by_author(github_client, mock_repo):
    """Test getting PRs filtered by author"""
    mock_pr1 = MagicMock()
    mock_pr1.user.login = "author1"
    mock_pr1.labels = []
    mock_pr1.base.ref = "main"
    
    mock_pr2 = MagicMock()
    mock_pr2.user.login = "author2"
    mock_pr2.labels = []
    mock_pr2.base.ref = "main"
    
    mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
    
    prs = github_client.get_open_prs(author="author1")
    
    assert len(prs) == 1
    assert prs[0].user.login == "author1"


def test_get_open_prs_filtered_by_base_branch(github_client, mock_repo):
    """Test getting PRs filtered by base branch"""
    mock_pr1 = MagicMock()
    mock_pr1.user.login = "author1"
    mock_pr1.base.ref = "main"
    mock_pr1.labels = []
    
    mock_pr2 = MagicMock()
    mock_pr2.user.login = "author2"
    mock_pr2.base.ref = "develop"
    mock_pr2.labels = []
    
    mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
    
    prs = github_client.get_open_prs(base="main")
    
    assert len(prs) == 1
    assert prs[0].base.ref == "main"


# ============================================================================
# TEST: GET RECENT COMMITS
# ============================================================================

def test_get_recent_commits_default(github_client, mock_repo):
    """Test getting commits from last 24 hours"""
    mock_commit1 = MagicMock()
    mock_commit1.sha = "abc123"
    mock_commit1.author.login = "author1"
    
    mock_commit2 = MagicMock()
    mock_commit2.sha = "def456"
    mock_commit2.author.login = "author2"
    
    mock_repo.get_commits.return_value = [mock_commit1, mock_commit2]
    
    commits = github_client.get_recent_commits()
    
    assert len(commits) == 2
    # Verify called with default branch and since parameter
    call_args = mock_repo.get_commits.call_args
    assert call_args[1]['sha'] == "main"
    assert 'since' in call_args[1]


def test_get_recent_commits_with_since(github_client, mock_repo):
    """Test getting commits since specific date"""
    since = datetime.now() - timedelta(days=7)
    
    mock_commit = MagicMock()
    mock_commit.sha = "abc123"
    mock_commit.author.login = "author1"
    
    mock_repo.get_commits.return_value = [mock_commit]
    
    commits = github_client.get_recent_commits(since=since)
    
    assert len(commits) == 1
    call_args = mock_repo.get_commits.call_args
    assert call_args[1]['since'] == since


def test_get_recent_commits_filtered_by_author(github_client, mock_repo):
    """Test getting commits filtered by author"""
    mock_commit1 = MagicMock()
    mock_commit1.author.login = "author1"
    
    mock_commit2 = MagicMock()
    mock_commit2.author.login = "author2"
    
    mock_repo.get_commits.return_value = [mock_commit1, mock_commit2]
    
    commits = github_client.get_recent_commits(author="author1")
    
    assert len(commits) == 1
    assert commits[0].author.login == "author1"


# ============================================================================
# TEST: RETRY LOGIC
# ============================================================================

def test_retry_on_rate_limit(github_client, mock_repo):
    """Test retry on rate limit exception"""
    # Mock rate limit exception with reset time
    rate_limit_error = RateLimitExceededException(
        status=403,
        data={"message": "Rate limit exceeded"},
        headers={}
    )
    rate_limit_error.reset_time = datetime.now() + timedelta(seconds=2)
    
    # First call raises rate limit, second succeeds
    mock_repo.create_issue.side_effect = [
        rate_limit_error,
        MagicMock(number=42)
    ]
    
    with patch('time.sleep'):  # Mock sleep to speed up test
        issue = github_client.create_issue("Test", "Body")
    
    assert issue.number == 42
    assert mock_repo.create_issue.call_count == 2


def test_retry_on_server_error(github_client, mock_repo):
    """Test retry on server errors (502, 503, 504)"""
    server_error = GithubException(
        status=503,
        data={"message": "Service unavailable"},
        headers={}
    )
    
    # First call fails, second succeeds
    mock_repo.create_issue.side_effect = [
        server_error,
        MagicMock(number=42)
    ]
    
    with patch('time.sleep'):
        issue = github_client.create_issue("Test", "Body")
    
    assert issue.number == 42
    assert mock_repo.create_issue.call_count == 2


def test_no_retry_on_client_error(github_client, mock_repo):
    """Test no retry on client errors (400, 404, 422)"""
    client_error = GithubException(
        status=404,
        data={"message": "Not found"},
        headers={}
    )
    
    mock_repo.create_issue.side_effect = client_error
    
    with pytest.raises(GithubException):
        github_client.create_issue("Test", "Body")
    
    # Should not retry on 404
    assert mock_repo.create_issue.call_count == 1


def test_max_retries_exceeded(github_client, mock_repo):
    """Test max retries exceeded raises exception"""
    server_error = GithubException(
        status=503,
        data={"message": "Service unavailable"},
        headers={}
    )
    
    # Always fail
    mock_repo.create_issue.side_effect = server_error
    
    with patch('time.sleep'):
        with pytest.raises(Exception, match="failed after 3 retries"):
            github_client.create_issue("Test", "Body")
    
    # Should try 3 times (initial + 2 retries)
    assert mock_repo.create_issue.call_count == 3


# ============================================================================
# TEST: HEALTH CHECK
# ============================================================================

def test_health_check_success(github_client):
    """Test health check returns rate limit info"""
    mock_rate_limit = MagicMock()
    mock_core = MagicMock()
    mock_core.limit = 5000
    mock_core.remaining = 4999
    mock_core.reset = datetime.now()
    mock_rate_limit.core = mock_core
    
    github_client.github.get_rate_limit = MagicMock(return_value=mock_rate_limit)
    
    health = github_client.health_check()
    
    assert health["status"] == "healthy"
    assert health["repository"] == "dlai-sd/WAOOAW"
    assert health["rate"]["limit"] == 5000
    assert health["rate"]["remaining"] == 4999
    assert health["authenticated"] is True


def test_health_check_failure(github_client):
    """Test health check handles errors"""
    github_client.github.get_rate_limit = MagicMock(
        side_effect=Exception("Connection failed")
    )
    
    health = github_client.health_check()
    
    assert health["status"] == "unhealthy"
    assert "Connection failed" in health["error"]
    assert health["authenticated"] is False


# ============================================================================
# TEST: GET DEFAULT CLIENT
# ============================================================================

def test_get_default_client(mock_github, mock_repo, monkeypatch):
    """Test getting client with default config"""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "dlai-sd/WAOOAW")
    
    mock_github_instance = mock_github.return_value
    mock_github_instance.get_repo.return_value = mock_repo
    
    client = get_default_client()
    
    assert client.token == "test_token"
    assert client.repo_name == "dlai-sd/WAOOAW"


# ============================================================================
# TEST: FILE CONTENT
# ============================================================================

def test_get_file_content(github_client, mock_repo):
    """Test getting file content from repository"""
    import base64
    
    mock_content_file = MagicMock()
    file_content = "print('Hello, World!')"
    mock_content_file.content = base64.b64encode(file_content.encode()).decode()
    
    mock_repo.get_contents.return_value = mock_content_file
    
    content = github_client.get_file_content("app/main.py")
    
    assert content == file_content
    mock_repo.get_contents.assert_called_once_with("app/main.py", ref="main")


def test_get_file_content_with_ref(github_client, mock_repo):
    """Test getting file content from specific ref"""
    import base64
    
    mock_content_file = MagicMock()
    file_content = "# README"
    mock_content_file.content = base64.b64encode(file_content.encode()).decode()
    
    mock_repo.get_contents.return_value = mock_content_file
    
    content = github_client.get_file_content("README.md", ref="develop")
    
    assert content == file_content
    mock_repo.get_contents.assert_called_once_with("README.md", ref="develop")


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 2.1 GitHub Client Test Coverage:

✅ Initialization (4 tests)
✅ Create issue (3 tests)
✅ Comment on PR (2 tests)
✅ Get open PRs (3 tests)
✅ Get recent commits (3 tests)
✅ Retry logic (4 tests)
✅ Health check (2 tests)
✅ Get default client (1 test)
✅ File content (2 tests)

Total: 24 unit tests ✅

All methods tested with mocked GitHub API.
Error handling, retries, and edge cases covered.
"""
