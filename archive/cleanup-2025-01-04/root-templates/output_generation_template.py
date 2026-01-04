"""
Output Generation Template - Week 3-4 Implementation
Make agents produce visible artifacts (GitHub issues, PR comments, reports)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from github import Github, Issue, PullRequest, Repository
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a rule violation found by agent"""
    rule_name: str
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: Optional[int]
    description: str
    recommendation: str
    layer: Optional[str] = None  # Layer 1, 2, 3 (for WowVision)
    
    def to_markdown(self) -> str:
        """Convert violation to markdown format"""
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': '💡'
        }
        emoji = severity_emoji.get(self.severity, '📋')
        
        md = f"### {emoji} {self.rule_name}\n\n"
        md += f"**Severity:** {self.severity.upper()}\n"
        md += f"**File:** `{self.file_path}`\n"
        if self.line_number:
            md += f"**Line:** {self.line_number}\n"
        if self.layer:
            md += f"**Layer:** {self.layer}\n"
        md += f"\n**Issue:**\n{self.description}\n"
        md += f"\n**Recommendation:**\n{self.recommendation}\n"
        
        return md


@dataclass
class AgentDecision:
    """Agent's decision result"""
    approved: bool
    confidence: float  # 0.0 to 1.0
    method: str  # deterministic, cached, llm
    cost: float  # USD
    duration_ms: int
    violations: List[Violation]
    notes: str


class OutputGenerator:
    """
    Mixin class for agents to generate visible outputs.
    
    Add to base_agent.py or use as mixin in WowVision Prime.
    """
    
    def __init__(self, github_token: str, repo_name: str):
        """Initialize GitHub connection"""
        self.github = Github(github_token)
        self.repo: Repository = self.github.get_repo(repo_name)
        logger.info(f"✅ OutputGenerator connected to {repo_name}")
    
    def create_github_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        assignees: Optional[List[str]] = None
    ) -> Issue:
        """
        Create GitHub issue for violations or escalations.
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: Labels to apply
            assignees: Users to assign
            
        Returns:
            Created Issue object
        """
        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels,
                assignees=assignees or []
            )
            
            logger.info(f"✅ Created issue #{issue.number}: {title}")
            return issue
        
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise
    
    def create_violation_issue(
        self,
        violations: List[Violation],
        file_path: str,
        commit_sha: str,
        agent_id: str
    ) -> Issue:
        """
        Create issue for vision violations.
        
        Args:
            violations: List of violations found
            file_path: File that has violations
            commit_sha: Commit hash
            agent_id: Which agent found violations
            
        Returns:
            Created Issue
        """
        # Categorize by severity
        critical = [v for v in violations if v.severity == 'critical']
        high = [v for v in violations if v.severity == 'high']
        medium = [v for v in violations if v.severity == 'medium']
        low = [v for v in violations if v.severity == 'low']
        
        # Build title
        if critical:
            title = f"🚨 CRITICAL: {len(critical)} violation(s) in {file_path}"
        elif high:
            title = f"⚠️ {len(high)} high-severity violation(s) in {file_path}"
        else:
            title = f"⚡ Violations found in {file_path}"
        
        # Build body
        body = f"## Vision Violations Detected\n\n"
        body += f"**Agent:** {agent_id}\n"
        body += f"**File:** `{file_path}`\n"
        body += f"**Commit:** {commit_sha}\n"
        body += f"**Total Violations:** {len(violations)}\n\n"
        
        body += "---\n\n"
        
        # Add violations by severity
        if critical:
            body += "## 🚨 Critical Issues\n\n"
            for v in critical:
                body += v.to_markdown() + "\n"
        
        if high:
            body += "## ⚠️ High Priority\n\n"
            for v in high:
                body += v.to_markdown() + "\n"
        
        if medium:
            body += "## ⚡ Medium Priority\n\n"
            for v in medium:
                body += v.to_markdown() + "\n"
        
        if low:
            body += "## 💡 Suggestions\n\n"
            for v in low:
                body += v.to_markdown() + "\n"
        
        # Footer
        body += "\n---\n\n"
        body += f"*Generated by {agent_id} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        body += f"*To resolve: Fix violations and update PR*"
        
        # Determine labels
        labels = ['vision-violation', f'agent:{agent_id}']
        if critical:
            labels.append('severity:critical')
        elif high:
            labels.append('severity:high')
        else:
            labels.append('severity:medium')
        
        # Create issue
        return self.create_github_issue(
            title=title,
            body=body,
            labels=labels
        )
    
    def comment_on_pr(
        self,
        pr_number: int,
        decision: AgentDecision,
        agent_id: str
    ):
        """
        Comment on PR with agent's decision.
        
        Args:
            pr_number: PR number
            decision: Agent's decision
            agent_id: Which agent
        """
        try:
            pr: PullRequest = self.repo.get_pull(pr_number)
            
            # Build comment
            if decision.approved:
                header = f"✅ **Approved by {agent_id}**\n\n"
                emoji = "✅"
            else:
                header = f"❌ **Blocked by {agent_id}**\n\n"
                emoji = "❌"
            
            comment = header
            comment += f"**Confidence:** {decision.confidence:.0%}\n"
            comment += f"**Method:** {decision.method}\n"
            comment += f"**Duration:** {decision.duration_ms}ms\n\n"
            
            if decision.violations:
                comment += f"## {emoji} Issues Found\n\n"
                for v in decision.violations:
                    comment += f"- **{v.severity.upper()}**: {v.rule_name}\n"
                    comment += f"  - File: `{v.file_path}`\n"
                    comment += f"  - {v.description}\n\n"
            
            if decision.notes:
                comment += f"## 📝 Notes\n\n{decision.notes}\n\n"
            
            # Footer
            comment += "\n---\n"
            comment += f"*{agent_id} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            # Post comment
            pr.create_issue_comment(comment)
            logger.info(f"✅ Commented on PR #{pr_number}")
        
        except Exception as e:
            logger.error(f"Failed to comment on PR #{pr_number}: {e}")
            raise
    
    def generate_daily_report(
        self,
        agent_id: str,
        date: datetime,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate daily report markdown.
        
        Args:
            agent_id: Agent name
            date: Report date
            metrics: Daily metrics
            
        Returns:
            Markdown report
        """
        report = f"# {agent_id} Daily Report\n\n"
        report += f"**Date:** {date.strftime('%Y-%m-%d')}\n\n"
        
        report += "## 📊 Activity Summary\n\n"
        report += f"- **Wake Cycles:** {metrics.get('wake_count', 0)}\n"
        report += f"- **Tasks Processed:** {metrics.get('tasks_processed', 0)}\n"
        report += f"- **Decisions Made:** {metrics.get('decisions_made', 0)}\n"
        report += f"- **Issues Created:** {metrics.get('issues_created', 0)}\n"
        report += f"- **PRs Reviewed:** {metrics.get('prs_reviewed', 0)}\n\n"
        
        report += "## 💰 Cost Analysis\n\n"
        report += f"- **Total Cost:** ${metrics.get('total_cost', 0):.4f}\n"
        report += f"- **Deterministic Decisions:** {metrics.get('deterministic_pct', 0):.0%} (${0:.4f})\n"
        report += f"- **Cached Decisions:** {metrics.get('cached_pct', 0):.0%} (${metrics.get('cached_cost', 0):.4f})\n"
        report += f"- **LLM Decisions:** {metrics.get('llm_pct', 0):.0%} (${metrics.get('llm_cost', 0):.4f})\n\n"
        
        report += "## 🎯 Decision Quality\n\n"
        report += f"- **Average Confidence:** {metrics.get('avg_confidence', 0):.0%}\n"
        report += f"- **Approvals:** {metrics.get('approvals', 0)}\n"
        report += f"- **Rejections:** {metrics.get('rejections', 0)}\n"
        report += f"- **Escalations:** {metrics.get('escalations', 0)}\n\n"
        
        if metrics.get('top_violations'):
            report += "## ⚠️ Top Violations\n\n"
            for rule, count in metrics['top_violations'].items():
                report += f"- **{rule}:** {count} times\n"
            report += "\n"
        
        report += "---\n"
        report += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return report
    
    def create_daily_report_issue(
        self,
        agent_id: str,
        date: datetime,
        metrics: Dict[str, Any]
    ) -> Issue:
        """Create issue with daily report"""
        report = self.generate_daily_report(agent_id, date, metrics)
        
        title = f"📊 {agent_id} Daily Report - {date.strftime('%Y-%m-%d')}"
        
        return self.create_github_issue(
            title=title,
            body=report,
            labels=['daily-report', f'agent:{agent_id}']
        )


# ============================================
# INTEGRATION WITH WOWVISION PRIME
# ============================================

"""
Add to waooaw/agents/wowvision_prime.py:

class WowVisionPrime(WAAOOWAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__('wowvision_prime', config)
        
        # Output generation
        self.output_generator = OutputGenerator(
            github_token=config['github_token'],
            repo_name=config['github_repo']
        )
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        '''Execute validation and CREATE OUTPUTS'''
        
        # 1. Validate file (existing logic)
        violations = self._validate_file(task['file_path'], task['content'])
        
        # 2. Make decision
        decision = AgentDecision(
            approved=len(violations) == 0,
            confidence=0.95,
            method='deterministic',
            cost=0.0,
            duration_ms=150,
            violations=violations,
            notes=f"Validated {task['file_path']} against Layer 1-3 rules"
        )
        
        # 3. CREATE OUTPUT (NEW!)
        if violations:
            # Create issue for violations
            issue = self.output_generator.create_violation_issue(
                violations=violations,
                file_path=task['file_path'],
                commit_sha=task.get('commit_sha', 'unknown'),
                agent_id='WowVision Prime'
            )
            logger.info(f"✅ Created issue #{issue.number} for violations")
        
        # 4. Comment on PR if PR number provided
        if task.get('pr_number'):
            self.output_generator.comment_on_pr(
                pr_number=task['pr_number'],
                decision=decision,
                agent_id='WowVision Prime'
            )
        
        return {
            'decision': decision,
            'issue_number': issue.number if violations else None
        }
    
    def generate_daily_report(self):
        '''Generate daily report (called by scheduler)'''
        metrics = self._collect_daily_metrics()
        
        self.output_generator.create_daily_report_issue(
            agent_id='WowVision Prime',
            date=datetime.now(),
            metrics=metrics
        )
"""


# ============================================
# EXAMPLE: Validation with Output
# ============================================

def example_validation_with_output():
    """Example: WowVision validates file and creates issue"""
    
    # Setup
    output_gen = OutputGenerator(
        github_token="ghp_xxx",
        repo_name="dlai-sd/WAOOAW"
    )
    
    # Simulate violations found
    violations = [
        Violation(
            rule_name="Brand Name Format",
            severity="critical",
            file_path="docs/README.md",
            line_number=5,
            description="Brand name 'waooaw' must be 'WAOOAW' (all caps)",
            recommendation="Change to 'WAOOAW' everywhere",
            layer="Layer 1"
        ),
        Violation(
            rule_name="Missing Tagline",
            severity="high",
            file_path="docs/README.md",
            line_number=None,
            description="Document missing brand tagline",
            recommendation="Add 'Agents Earn Your Business' tagline",
            layer="Layer 1"
        )
    ]
    
    # Create issue
    issue = output_gen.create_violation_issue(
        violations=violations,
        file_path="docs/README.md",
        commit_sha="abc123",
        agent_id="WowVision Prime"
    )
    
    print(f"✅ Created issue #{issue.number}: {issue.title}")
    
    # Create decision
    decision = AgentDecision(
        approved=False,
        confidence=0.98,
        method="deterministic",
        cost=0.0,
        duration_ms=120,
        violations=violations,
        notes="Critical Layer 1 violations found"
    )
    
    # Comment on PR
    output_gen.comment_on_pr(
        pr_number=42,
        decision=decision,
        agent_id="WowVision Prime"
    )
    
    print("✅ Commented on PR #42")


if __name__ == "__main__":
    example_validation_with_output()
