"""GitHub integration module"""

from .github_client import GitHubClient, get_default_client, retry_on_github_error

__all__ = ["GitHubClient", "get_default_client", "retry_on_github_error"]
