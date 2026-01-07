"""
PR Review Workflow - Story 2.3

Orchestrates PR review process using GitHub helpers and issue templates.
Part of Epic 2: GitHub Integration.
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .helpers import GitHubHelpers
from .templates import IssueTemplates

logger = logging.getLogger(__name__)


@dataclass
class PRReviewResult:
    """Result of PR review."""
    approved: bool
    violations: List[Dict[str, Any]]
    escalations: List[Dict[str, Any]]
    comments_posted: List[int]
    issues_created: List[int]
    summary: str


class PRReviewWorkflow:
    """
    Orchestrates pull request review workflow.
    
    Steps:
    1. Get PR files changed
    2. Analyze each file (vision compliance, code standards)
    3. Post comments on PR
    4. Create violation issues if needed
    5. Escalate if ambiguity detected
    6. Approve or request changes
    """
    
    def __init__(self, github_helpers: GitHubHelpers):
        """
        Initialize PR review workflow.
        
        Args:
            github_helpers: GitHubHelpers instance
        """
        self.gh = github_helpers
        logger.info("PRReviewWorkflow initialized")
    
    def review_pr(
        self,
        pr_number: int,
        check_vision: bool = True,
        check_standards: bool = True,
        auto_comment: bool = True,
        create_issues: bool = True
    ) -> PRReviewResult:
        """
        Review a pull request.
        
        Args:
            pr_number: PR number to review
            check_vision: Check vision compliance
            check_standards: Check code standards
            auto_comment: Auto-post comments on PR
            create_issues: Auto-create violation issues
            
        Returns:
            PRReviewResult with approval status and details
        """
        logger.info(f"Starting PR review: #{pr_number}")
        
        violations = []
        escalations = []
        comments_posted = []
        issues_created = []
        
        # Step 1: Get PR files
        files = self.gh.get_pr_files(pr_number)
        logger.info(f"Analyzing {len(files)} files in PR #{pr_number}")
        
        # Step 2: Analyze files
        for file in files:
            file_violations = self._analyze_file(
                file,
                check_vision=check_vision,
                check_standards=check_standards
            )
            violations.extend(file_violations)
        
        # Step 3: Check for escalations
        if self._needs_escalation(files, violations):
            escalation = self._create_escalation(pr_number, files, violations)
            escalations.append(escalation)
            
            if create_issues:
                issue = self.gh.create_issue(**escalation)
                issues_created.append(issue.number)
                logger.info(f"Created escalation issue #{issue.number}")
        
        # Step 4: Create violation issues
        if create_issues:
            for violation in violations:
                if violation["severity"] in ["high", "critical"]:
                    issue_data = IssueTemplates.violation_issue(**violation)
                    issue = self.gh.create_issue(**issue_data)
                    issues_created.append(issue.number)
                    logger.info(f"Created violation issue #{issue.number}")
        
        # Step 5: Post PR comment
        if auto_comment:
            comment_body = self._generate_review_comment(
                violations=violations,
                escalations=escalations,
                issues_created=issues_created
            )
            comment = self.gh.comment_on_pr(pr_number, comment_body)
            comments_posted.append(comment.id)
        
        # Step 6: Determine approval
        approved = self._should_approve(violations, escalations)
        
        summary = self._generate_summary(
            files_count=len(files),
            violations_count=len(violations),
            escalations_count=len(escalations),
            approved=approved
        )
        
        logger.info(f"PR review complete: approved={approved}, violations={len(violations)}")
        
        return PRReviewResult(
            approved=approved,
            violations=violations,
            escalations=escalations,
            comments_posted=comments_posted,
            issues_created=issues_created,
            summary=summary
        )
    
    def _analyze_file(
        self,
        file: Dict[str, Any],
        check_vision: bool = True,
        check_standards: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single file for violations.
        
        Args:
            file: File dict from get_pr_files
            check_vision: Check vision compliance
            check_standards: Check code standards
            
        Returns:
            List of violation dicts
        """
        violations = []
        filename = file["filename"]
        
        # Skip non-code files
        if not self._is_code_file(filename):
            return violations
        
        # Check for common issues
        if check_standards:
            # Large file check
            if file["additions"] > 500:
                violations.append({
                    "violation_type": "Large PR",
                    "file_path": filename,
                    "description": f"File has {file['additions']} additions. Consider breaking into smaller PRs.",
                    "severity": "medium",
                    "context": {"additions": file["additions"]}
                })
            
            # Deleted file without explanation
            if file["status"] == "removed" and file["deletions"] > 100:
                violations.append({
                    "violation_type": "Large Deletion",
                    "file_path": filename,
                    "description": f"File deleted with {file['deletions']} lines. Ensure this is intentional.",
                    "severity": "low",
                    "context": {"deletions": file["deletions"]}
                })
        
        if check_vision:
            # Check for README changes (should align with vision)
            if "README" in filename.upper():
                violations.append({
                    "violation_type": "Documentation Change",
                    "file_path": filename,
                    "description": "README modified. Verify alignment with vision.yaml.",
                    "severity": "low",
                    "policy_reference": "vision.yaml"
                })
        
        return violations
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file."""
        code_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".rb"]
        return any(filename.endswith(ext) for ext in code_extensions)
    
    def _needs_escalation(
        self,
        files: List[Dict[str, Any]],
        violations: List[Dict[str, Any]]
    ) -> bool:
        """
        Determine if PR needs human escalation.
        
        Args:
            files: List of files changed
            violations: List of violations found
            
        Returns:
            True if escalation needed
        """
        # Escalate if critical violations
        if any(v["severity"] == "critical" for v in violations):
            return True
        
        # Escalate if very large PR (>20 files)
        if len(files) > 20:
            return True
        
        # Escalate if many violations (>5)
        if len(violations) > 5:
            return True
        
        return False
    
    def _create_escalation(
        self,
        pr_number: int,
        files: List[Dict[str, Any]],
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create escalation issue data."""
        reason = f"PR #{pr_number} requires human review:\n"
        reason += f"- {len(files)} files changed\n"
        reason += f"- {len(violations)} violations detected\n"
        
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        if critical_violations:
            reason += f"- {len(critical_violations)} CRITICAL violations\n"
        
        return IssueTemplates.escalation_issue(
            trigger=f"PR #{pr_number} Review",
            reason=reason,
            pr_number=pr_number,
            files_affected=[f["filename"] for f in files[:10]],  # Max 10 files
            action_required="Review violations and approve/reject PR"
        )
    
    def _generate_review_comment(
        self,
        violations: List[Dict[str, Any]],
        escalations: List[Dict[str, Any]],
        issues_created: List[int]
    ) -> str:
        """Generate PR review comment."""
        comment = "## 🤖 WowVision Prime Review\n\n"
        
        if not violations:
            comment += "✅ **No violations detected!** This PR looks good.\n\n"
            comment += "**Next Steps:**\n"
            comment += "- Verify tests are passing\n"
            comment += "- Merge when ready\n"
        else:
            comment += f"⚠️ **{len(violations)} violation(s) detected**\n\n"
            
            # Group by severity
            critical = [v for v in violations if v["severity"] == "critical"]
            high = [v for v in violations if v["severity"] == "high"]
            medium = [v for v in violations if v["severity"] == "medium"]
            low = [v for v in violations if v["severity"] == "low"]
            
            if critical:
                comment += f"🚨 **CRITICAL ({len(critical)})**: Must fix before merge\n"
            if high:
                comment += f"🔴 **HIGH ({len(high)})**: Should fix before merge\n"
            if medium:
                comment += f"🟠 **MEDIUM ({len(medium)})**: Consider fixing\n"
            if low:
                comment += f"🟡 **LOW ({len(low)})**: Optional improvements\n"
            
            comment += "\n"
        
        if issues_created:
            comment += "### 📋 Issues Created\n\n"
            for issue_num in issues_created:
                comment += f"- #{issue_num}\n"
            comment += "\n"
        
        if escalations:
            comment += "### 🚀 Human Input Required\n\n"
            comment += "This PR has been escalated for human review. "
            comment += "Please review the escalation issues above.\n\n"
        
        comment += "---\n"
        comment += "*Automated review by WowVision Prime 🎯*"
        
        return comment
    
    def _should_approve(
        self,
        violations: List[Dict[str, Any]],
        escalations: List[Dict[str, Any]]
    ) -> bool:
        """Determine if PR should be approved."""
        # Don't approve if escalated
        if escalations:
            return False
        
        # Don't approve if critical/high violations
        if any(v["severity"] in ["critical", "high"] for v in violations):
            return False
        
        # Approve if no violations or only low/medium
        return True
    
    def _generate_summary(
        self,
        files_count: int,
        violations_count: int,
        escalations_count: int,
        approved: bool
    ) -> str:
        """Generate summary string."""
        summary = f"Reviewed {files_count} file(s). "
        summary += f"Found {violations_count} violation(s). "
        
        if escalations_count:
            summary += f"Escalated ({escalations_count} issue(s)). "
        
        summary += "APPROVED." if approved else "CHANGES REQUESTED."
        
        return summary
