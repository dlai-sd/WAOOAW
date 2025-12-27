"""
GitHub Issue Templates - Story 2.2

Markdown templates for common GitHub issues created by agents.
Part of Epic 2: GitHub Integration.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class IssueTemplates:
    """
    Templates for GitHub issues created by agents.
    
    Provides formatted markdown for violations, escalations, and approvals.
    """
    
    @staticmethod
    def violation_issue(
        violation_type: str,
        file_path: str,
        description: str,
        severity: str = "medium",
        policy_reference: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a violation issue (architectural/code standard violation).
        
        Args:
            violation_type: Type of violation (e.g., "Vision Mismatch", "Code Standard")
            file_path: File where violation occurred
            description: Detailed description
            severity: low, medium, high, critical
            policy_reference: Reference to policy document (e.g., "vision.yaml:L23")
            suggested_fix: Suggested resolution
            context: Additional context (line numbers, code snippets)
            
        Returns:
            Dict with 'title', 'body', 'labels'
        """
        severity_emoji = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }
        
        title = f"{severity_emoji.get(severity, '⚠️')} {violation_type}: {file_path}"
        
        body = f"""## 🔍 Violation Detected

**Type**: {violation_type}  
**File**: `{file_path}`  
**Severity**: {severity.upper()}  
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

### 📋 Description

{description}

"""
        
        if policy_reference:
            body += f"""### 📚 Policy Reference

Violates: `{policy_reference}`

"""
        
        if suggested_fix:
            body += f"""### 💡 Suggested Fix

{suggested_fix}

"""
        
        if context:
            body += "### 📊 Context\n\n"
            for key, value in context.items():
                body += f"- **{key}**: {value}\n"
            body += "\n"
        
        body += """---

### ✅ Resolution Steps

1. Review the violation details above
2. Apply the suggested fix (if provided)
3. Ensure compliance with project policies
4. Comment on this issue when resolved
5. Close the issue after validation

**Agent**: WowVision Prime 🎯  
**Auto-generated**: This issue was created by the WAOOAW agent system
"""
        
        labels = [
            "violation",
            f"severity-{severity}",
            "agent-generated"
        ]
        
        return {
            "title": title,
            "body": body,
            "labels": labels
        }
    
    @staticmethod
    def escalation_issue(
        trigger: str,
        reason: str,
        pr_number: Optional[int] = None,
        files_affected: Optional[List[str]] = None,
        action_required: Optional[str] = None,
        agent_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an escalation issue (agent needs human input).
        
        Args:
            trigger: What triggered escalation (e.g., "@wowvision-prime", "ambiguity")
            reason: Why escalation is needed
            pr_number: Related PR number (if applicable)
            files_affected: List of files needing attention
            action_required: What human should do
            agent_context: Agent's current state/context
            
        Returns:
            Dict with 'title', 'body', 'labels'
        """
        title = f"🚀 Escalation: {trigger}"
        
        body = f"""## 🚀 Human Input Required

**Trigger**: {trigger}  
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

### 🤔 Why Escalation?

{reason}

"""
        
        if pr_number:
            body += f"""### 🔗 Related PR

Pull Request: #{pr_number}

"""
        
        if files_affected:
            body += "### 📁 Files Requiring Attention\n\n"
            for file in files_affected:
                body += f"- `{file}`\n"
            body += "\n"
        
        if action_required:
            body += f"""### ✨ Action Required

{action_required}

"""
        
        if agent_context:
            body += "### 🤖 Agent Context\n\n"
            body += "```json\n"
            import json
            body += json.dumps(agent_context, indent=2)
            body += "\n```\n\n"
        
        body += """---

### 📝 Response Format

Please respond with:
1. Your decision/guidance
2. Any additional context needed
3. Tag `@wowvision-prime` when ready for agent to continue

**Agent**: WowVision Prime 🎯  
**Status**: ⏸️ Paused - Awaiting human input
"""
        
        labels = [
            "escalation",
            "needs-human-input",
            "agent-paused",
            "priority-high"
        ]
        
        return {
            "title": title,
            "body": body,
            "labels": labels
        }
    
    @staticmethod
    def approval_issue(
        task_completed: str,
        summary: str,
        pr_number: Optional[int] = None,
        metrics: Optional[Dict[str, Any]] = None,
        deliverables: Optional[List[str]] = None,
        next_steps: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an approval issue (agent completed task, needs sign-off).
        
        Args:
            task_completed: What was completed
            summary: Summary of work done
            pr_number: Related PR number (if applicable)
            metrics: Performance metrics (tests passing, coverage, etc.)
            deliverables: List of deliverables/artifacts
            next_steps: Suggested next steps
            
        Returns:
            Dict with 'title', 'body', 'labels'
        """
        title = f"✅ Approval Request: {task_completed}"
        
        body = f"""## ✅ Task Complete - Approval Requested

**Task**: {task_completed}  
**Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

### 📊 Summary

{summary}

"""
        
        if pr_number:
            body += f"""### 🔗 Pull Request

PR #{pr_number} - Ready for review

"""
        
        if metrics:
            body += "### 📈 Metrics\n\n"
            for key, value in metrics.items():
                body += f"- **{key}**: {value}\n"
            body += "\n"
        
        if deliverables:
            body += "### 📦 Deliverables\n\n"
            for item in deliverables:
                body += f"- ✅ {item}\n"
            body += "\n"
        
        if next_steps:
            body += f"""### 🎯 Suggested Next Steps

{next_steps}

"""
        
        body += """---

### 👍 Approval Process

**To approve**: Comment "LGTM" or "Approved" and close this issue  
**To request changes**: Comment with feedback and tag `@wowvision-prime`

**Agent**: WowVision Prime 🎯  
**Status**: ✅ Complete - Awaiting approval
"""
        
        labels = [
            "approval-request",
            "needs-review",
            "agent-complete"
        ]
        
        return {
            "title": title,
            "body": body,
            "labels": labels
        }
    
    @staticmethod
    def status_update_comment(
        status: str,
        details: str,
        progress: Optional[int] = None,
        eta: Optional[str] = None,
        blockers: Optional[List[str]] = None
    ) -> str:
        """
        Create a status update comment for existing issue/PR.
        
        Args:
            status: Current status (e.g., "in-progress", "blocked", "complete")
            details: Status details
            progress: Progress percentage (0-100)
            eta: Estimated completion time
            blockers: List of blockers (if any)
            
        Returns:
            Formatted markdown comment
        """
        status_emoji = {
            "in-progress": "⏳",
            "blocked": "🚫",
            "complete": "✅",
            "paused": "⏸️",
            "reviewing": "👀"
        }
        
        comment = f"""## {status_emoji.get(status, '📝')} Status Update

**Status**: {status.upper()}  
**Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

{details}

"""
        
        if progress is not None:
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            comment += f"**Progress**: {bar} {progress}%\n\n"
        
        if eta:
            comment += f"**ETA**: {eta}\n\n"
        
        if blockers:
            comment += "### 🚫 Blockers\n\n"
            for blocker in blockers:
                comment += f"- {blocker}\n"
            comment += "\n"
        
        comment += "---\n*Agent: WowVision Prime 🎯*"
        
        return comment
