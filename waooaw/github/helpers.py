"""
GitHub Helper Functions - Story 2.1

Wrapper functions for common GitHub operations using PyGithub.
Part of Epic 2: GitHub Integration.
"""
import logging
from typing import List, Dict, Optional, Any
from github import Github, GithubException
from github.Repository import Repository
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.IssueComment import IssueComment

logger = logging.getLogger(__name__)


class GitHubHelpers:
    """
    Helper class for GitHub operations.
    
    Wraps PyGithub with error handling, retries, and logging.
    Used by agents to interact with GitHub repositories.
    """
    
    def __init__(self, github_token: str, repo_name: str):
        """
        Initialize GitHub helpers.
        
        Args:
            github_token: GitHub personal access token
            repo_name: Repository name (owner/repo format)
        """
        self.github_client = Github(github_token)
        self.repo: Repository = self.github_client.get_repo(repo_name)
        self.repo_name = repo_name
        
        logger.info(f"GitHubHelpers initialized for {repo_name}")
    
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Issue:
        """
        Create a new GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of label names
            assignees: List of usernames to assign
            
        Returns:
            Created Issue object
            
        Raises:
            GithubException: If creation fails
        """
        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or []
            )
            
            logger.info(
                f"Created issue #{issue.number}: {title}",
                extra={
                    "issue_number": issue.number,
                    "labels": labels,
                    "assignees": assignees
                }
            )
            
            return issue
            
        except GithubException as e:
            logger.error(f"Failed to create issue: {e}", exc_info=True)
            raise
    
    def comment_on_issue(
        self,
        issue_number: int,
        comment_body: str
    ) -> IssueComment:
        """
        Add a comment to an existing issue.
        
        Args:
            issue_number: Issue number
            comment_body: Comment text (markdown)
            
        Returns:
            Created IssueComment object
            
        Raises:
            GithubException: If comment fails
        """
        try:
            issue = self.repo.get_issue(issue_number)
            comment = issue.create_comment(comment_body)
            
            logger.info(
                f"Commented on issue #{issue_number}",
                extra={
                    "issue_number": issue_number,
                    "comment_id": comment.id
                }
            )
            
            return comment
            
        except GithubException as e:
            logger.error(
                f"Failed to comment on issue #{issue_number}: {e}",
                exc_info=True
            )
            raise
    
    def comment_on_pr(
        self,
        pr_number: int,
        comment_body: str
    ) -> IssueComment:
        """
        Add a comment to a pull request.
        
        Args:
            pr_number: PR number
            comment_body: Comment text (markdown)
            
        Returns:
            Created IssueComment object
            
        Note:
            PRs are issues, so this uses issue.create_comment()
        """
        return self.comment_on_issue(pr_number, comment_body)
    
    def get_pr_files(
        self,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get list of files changed in a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of file dicts with: filename, status, additions, deletions, changes
            
        Raises:
            GithubException: If PR not found
        """
        try:
            pr = self.repo.get_pull(pr_number)
            files = pr.get_files()
            
            file_list = []
            for file in files:
                file_list.append({
                    "filename": file.filename,
                    "status": file.status,  # added, removed, modified, renamed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, "patch") else None
                })
            
            logger.info(
                f"Retrieved {len(file_list)} files from PR #{pr_number}",
                extra={
                    "pr_number": pr_number,
                    "file_count": len(file_list)
                }
            )
            
            return file_list
            
        except GithubException as e:
            logger.error(
                f"Failed to get PR #{pr_number} files: {e}",
                exc_info=True
            )
            raise
    
    def get_file_content(
        self,
        file_path: str,
        ref: str = "main"
    ) -> str:
        """
        Get content of a file from the repository.
        
        Args:
            file_path: Path to file in repo
            ref: Branch/tag/commit reference (default: main)
            
        Returns:
            File content as string
            
        Raises:
            GithubException: If file not found
        """
        try:
            content = self.repo.get_contents(file_path, ref=ref)
            
            if isinstance(content, list):
                # Directory, not a file
                raise ValueError(f"{file_path} is a directory, not a file")
            
            decoded_content = content.decoded_content.decode("utf-8")
            
            logger.info(
                f"Retrieved file: {file_path} @ {ref}",
                extra={
                    "file_path": file_path,
                    "ref": ref,
                    "size": len(decoded_content)
                }
            )
            
            return decoded_content
            
        except GithubException as e:
            logger.error(
                f"Failed to get file {file_path} @ {ref}: {e}",
                exc_info=True
            )
            raise
    
    def list_open_prs(
        self,
        limit: int = 10
    ) -> List[PullRequest]:
        """
        List open pull requests.
        
        Args:
            limit: Maximum number of PRs to return
            
        Returns:
            List of PullRequest objects
        """
        try:
            prs = self.repo.get_pulls(state="open", sort="created", direction="desc")
            pr_list = list(prs[:limit])
            
            logger.info(
                f"Retrieved {len(pr_list)} open PRs",
                extra={"pr_count": len(pr_list)}
            )
            
            return pr_list
            
        except GithubException as e:
            logger.error(f"Failed to list open PRs: {e}", exc_info=True)
            raise
    
    def add_labels_to_issue(
        self,
        issue_number: int,
        labels: List[str]
    ):
        """
        Add labels to an issue.
        
        Args:
            issue_number: Issue number
            labels: List of label names to add
        """
        try:
            issue = self.repo.get_issue(issue_number)
            issue.add_to_labels(*labels)
            
            logger.info(
                f"Added labels to issue #{issue_number}: {labels}",
                extra={
                    "issue_number": issue_number,
                    "labels": labels
                }
            )
            
        except GithubException as e:
            logger.error(
                f"Failed to add labels to issue #{issue_number}: {e}",
                exc_info=True
            )
            raise
    
    def close_issue(
        self,
        issue_number: int,
        comment: Optional[str] = None
    ):
        """
        Close an issue (optionally with a comment).
        
        Args:
            issue_number: Issue number
            comment: Optional closing comment
        """
        try:
            issue = self.repo.get_issue(issue_number)
            
            if comment:
                issue.create_comment(comment)
            
            issue.edit(state="closed")
            
            logger.info(
                f"Closed issue #{issue_number}",
                extra={"issue_number": issue_number}
            )
            
        except GithubException as e:
            logger.error(
                f"Failed to close issue #{issue_number}: {e}",
                exc_info=True
            )
            raise
