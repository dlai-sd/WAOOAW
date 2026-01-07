"""
GitHub API Client for WAOOAW Platform

Provides high-level interface to GitHub API for agent operations:
- Create issues
- Comment on PRs
- Fetch commits, PRs, issues
- Error handling with exponential backoff

Uses PyGithub library with retry logic and rate limit handling.
"""

import os
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Commit import Commit


logger = logging.getLogger(__name__)


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_on_github_error(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Retry decorator for GitHub API calls with exponential backoff.
    
    Retries on:
    - RateLimitExceededException
    - Network errors (ConnectionError, TimeoutError)
    - Server errors (502, 503, 504)
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
    
    Usage:
        @retry_on_github_error(max_retries=3)
        def create_issue(...):
            # GitHub API call
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = 1.0  # Initial delay in seconds
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                
                except RateLimitExceededException as e:
                    # Handle rate limit: wait until reset time
                    reset_time = e.reset_time if hasattr(e, 'reset_time') else None
                    if reset_time:
                        wait_time = (reset_time - datetime.now()).total_seconds()
                        wait_time = max(wait_time, 60)  # At least 1 minute
                        logger.warning(
                            f"⏱️ GitHub rate limit exceeded. "
                            f"Waiting {wait_time:.0f}s until reset..."
                        )
                        time.sleep(wait_time)
                    else:
                        time.sleep(delay)
                    
                    retries += 1
                    delay *= backoff_factor
                
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(
                        f"🔄 Network error in {func.__name__}: {e}. "
                        f"Retry {retries + 1}/{max_retries} in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    retries += 1
                    delay *= backoff_factor
                
                except GithubException as e:
                    # Retry on server errors (502, 503, 504)
                    if e.status in [502, 503, 504]:
                        logger.warning(
                            f"🔄 GitHub server error {e.status} in {func.__name__}. "
                            f"Retry {retries + 1}/{max_retries} in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        retries += 1
                        delay *= backoff_factor
                    else:
                        # Don't retry on client errors (400, 401, 403, 404)
                        raise
                
                except Exception as e:
                    # Don't retry on unknown errors
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise
            
            # Max retries exceeded
            logger.error(
                f"❌ Max retries ({max_retries}) exceeded for {func.__name__}"
            )
            raise Exception(f"GitHub API call failed after {max_retries} retries")
        
        return wrapper
    return decorator


# ============================================================================
# GITHUB CLIENT
# ============================================================================

class GitHubClient:
    """
    High-level GitHub API client with retry logic and error handling.
    
    Usage:
        client = GitHubClient(token=os.getenv("GITHUB_TOKEN"), repo="dlai-sd/WAOOAW")
        
        # Create issue
        issue = client.create_issue(
            title="🚨 Vision Violation: app/main.py",
            body="File violates project vision...",
            labels=["vision-violation", "agent-escalation"]
        )
        
        # Comment on PR
        client.comment_on_pr(
            pr_number=42,
            comment="✅ Vision compliant. All checks passed."
        )
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None
    ):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (or uses GITHUB_TOKEN env var)
            repo: Repository in format "owner/repo" (or uses GITHUB_REPOSITORY env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or pass token parameter."
            )
        
        self.repo_name = repo or os.getenv("GITHUB_REPOSITORY")
        if not self.repo_name:
            raise ValueError(
                "Repository required. Set GITHUB_REPOSITORY env var or pass repo parameter."
            )
        
        # Initialize PyGithub
        self.github = Github(self.token, per_page=100)
        self.repo: Repository = self.github.get_repo(self.repo_name)
        
        logger.info(f"✅ GitHubClient initialized for {self.repo_name}")
    
    # ========================================================================
    # ISSUE OPERATIONS
    # ========================================================================
    
    @retry_on_github_error(max_retries=3)
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> Issue:
        """
        Create a GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body (markdown supported)
            labels: List of label names to add
            assignee: GitHub username to assign
        
        Returns:
            Created GitHub Issue object
        
        Raises:
            GithubException: On API errors (404, 422, etc.)
        
        Example:
            issue = client.create_issue(
                title="🚨 Vision Violation: app/main.py",
                body="**File**: `app/main.py`\\n**Violation**: Missing docstrings",
                labels=["vision-violation", "agent-escalation"],
                assignee="dlai-sd"
            )
            print(f"Created issue #{issue.number}")
        """
        logger.info(f"📝 Creating issue: {title}")
        
        # Create issue
        issue = self.repo.create_issue(
            title=title,
            body=body,
            labels=labels or [],
            assignee=assignee
        )
        
        logger.info(f"✅ Created issue #{issue.number}: {title}")
        return issue
    
    @retry_on_github_error(max_retries=3)
    def get_issue(self, issue_number: int) -> Issue:
        """
        Get issue by number.
        
        Args:
            issue_number: Issue number
        
        Returns:
            GitHub Issue object
        """
        return self.repo.get_issue(issue_number)
    
    @retry_on_github_error(max_retries=3)
    def comment_on_issue(self, issue_number: int, comment: str):
        """
        Add comment to issue.
        
        Args:
            issue_number: Issue number
            comment: Comment text (markdown supported)
        """
        issue = self.repo.get_issue(issue_number)
        issue.create_comment(comment)
        logger.info(f"💬 Commented on issue #{issue_number}")
    
    # ========================================================================
    # PULL REQUEST OPERATIONS
    # ========================================================================
    
    @retry_on_github_error(max_retries=3)
    def comment_on_pr(self, pr_number: int, comment: str):
        """
        Add comment to pull request.
        
        Args:
            pr_number: PR number
            comment: Comment text (markdown supported)
        
        Example:
            client.comment_on_pr(
                pr_number=42,
                comment="✅ Vision compliant. All checks passed."
            )
        """
        logger.info(f"💬 Commenting on PR #{pr_number}")
        
        pr = self.repo.get_pull(pr_number)
        pr.create_issue_comment(comment)
        
        logger.info(f"✅ Commented on PR #{pr_number}")
    
    @retry_on_github_error(max_retries=3)
    def get_open_prs(
        self,
        author: Optional[str] = None,
        label: Optional[str] = None,
        base: Optional[str] = None
    ) -> List[PullRequest]:
        """
        Get list of open pull requests with optional filters.
        
        Args:
            author: Filter by author username
            label: Filter by label name
            base: Filter by base branch (e.g., "main")
        
        Returns:
            List of open PullRequest objects
        
        Example:
            # Get all open PRs
            prs = client.get_open_prs()
            
            # Get PRs by author
            prs = client.get_open_prs(author="dlai-sd")
            
            # Get PRs targeting main branch
            prs = client.get_open_prs(base="main")
        """
        logger.info(f"🔍 Fetching open PRs (author={author}, label={label}, base={base})")
        
        # Get all open PRs
        prs = list(self.repo.get_pulls(state="open", sort="created", direction="desc"))
        
        # Apply filters
        if author:
            prs = [pr for pr in prs if pr.user.login == author]
        
        if label:
            prs = [pr for pr in prs if label in [l.name for l in pr.labels]]
        
        if base:
            prs = [pr for pr in prs if pr.base.ref == base]
        
        logger.info(f"✅ Found {len(prs)} open PRs")
        return prs
    
    @retry_on_github_error(max_retries=3)
    def get_pr(self, pr_number: int) -> PullRequest:
        """
        Get pull request by number.
        
        Args:
            pr_number: PR number
        
        Returns:
            GitHub PullRequest object
        """
        return self.repo.get_pull(pr_number)
    
    # ========================================================================
    # COMMIT OPERATIONS
    # ========================================================================
    
    @retry_on_github_error(max_retries=3)
    def get_recent_commits(
        self,
        since: Optional[datetime] = None,
        author: Optional[str] = None,
        branch: Optional[str] = None
    ) -> List[Commit]:
        """
        Get recent commits with optional filters.
        
        Args:
            since: Get commits after this datetime (default: last 24 hours)
            author: Filter by author username
            branch: Filter by branch name (default: default branch)
        
        Returns:
            List of Commit objects (newest first)
        
        Example:
            # Get commits from last 24 hours
            commits = client.get_recent_commits()
            
            # Get commits from last 7 days
            from datetime import datetime, timedelta
            since = datetime.now() - timedelta(days=7)
            commits = client.get_recent_commits(since=since)
            
            # Get commits by author
            commits = client.get_recent_commits(author="dlai-sd")
        """
        if since is None:
            since = datetime.now() - timedelta(hours=24)
        
        logger.info(f"🔍 Fetching commits since {since} (author={author}, branch={branch})")
        
        # Get commits from branch
        branch_ref = branch or self.repo.default_branch
        commits = list(self.repo.get_commits(sha=branch_ref, since=since))
        
        # Filter by author
        if author:
            commits = [c for c in commits if c.author and c.author.login == author]
        
        logger.info(f"✅ Found {len(commits)} commits")
        return commits
    
    # ========================================================================
    # REPOSITORY OPERATIONS
    # ========================================================================
    
    @retry_on_github_error(max_retries=3)
    def get_file_content(self, file_path: str, ref: Optional[str] = None) -> str:
        """
        Get file content from repository.
        
        Args:
            file_path: Path to file in repository
            ref: Git ref (branch, tag, commit SHA). Default: default branch
        
        Returns:
            File content as string
        
        Example:
            content = client.get_file_content("app/main.py")
            content = client.get_file_content("README.md", ref="develop")
        """
        ref = ref or self.repo.default_branch
        content_file = self.repo.get_contents(file_path, ref=ref)
        
        # Decode base64 content
        import base64
        content = base64.b64decode(content_file.content).decode("utf-8")
        return content
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check GitHub API connectivity and rate limits.
        
        Returns:
            Health status dictionary with rate limit info
        
        Example:
            health = client.health_check()
            print(f"Rate limit: {health['rate']['remaining']}/{health['rate']['limit']}")
        """
        try:
            rate_limit = self.github.get_rate_limit()
            core = rate_limit.core
            
            return {
                "status": "healthy",
                "repository": self.repo_name,
                "rate": {
                    "limit": core.limit,
                    "remaining": core.remaining,
                    "reset": core.reset.isoformat() if core.reset else None
                },
                "authenticated": True
            }
        except Exception as e:
            logger.error(f"❌ GitHub health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "authenticated": False
            }
    
    def close(self):
        """Close GitHub connection"""
        # PyGithub doesn't have explicit close, but we can clear references
        self.github = None
        self.repo = None
        logger.info("✅ GitHubClient closed")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_default_client() -> GitHubClient:
    """
    Get GitHubClient with default configuration from environment variables.
    
    Requires:
        - GITHUB_TOKEN env var
        - GITHUB_REPOSITORY env var (format: "owner/repo")
    
    Returns:
        Configured GitHubClient instance
    
    Example:
        client = get_default_client()
        issue = client.create_issue("Test issue", "Test body")
    """
    return GitHubClient()
