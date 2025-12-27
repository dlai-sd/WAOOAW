"""
WowVision Prime - Vision Guardian Agent

First production agent inheriting from WAAOOWAgent base class.

Specialization: Enforce 3-layer vision stack across platform
Role: Platform conscience
Responsibilities:
- Validate all file creations against vision
- Review PRs for vision compliance
- Process human escalations
- Manage Layer 2 policies autonomously
- Learn vision violation patterns
"""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

from waooaw.agents.base_agent import WAAOOWAgent, Decision, AgentSpecialization
from waooaw.agents.event_types import (
    EVENT_FILE_CREATED,
    EVENT_FILE_UPDATED,
    EVENT_PR_OPENED,
    EVENT_ISSUE_COMMENT,
    EVENT_COMMIT_PUSHED,
)

logger = logging.getLogger(__name__)


class WowVisionPrime(WAAOOWAgent):
    """
    Vision Guardian Agent - First production agent inheriting from WAAOOWAgent.

    Specialization: Vision enforcement
    Role: Platform conscience
    Responsibilities:
    - Validate all file creations against vision
    - Review PRs for vision compliance
    - Process human escalations
    - Manage Layer 2 policies autonomously
    - Learn vision violation patterns
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(agent_id="WowVision-Prime", config=config)

        # WowVision-specific components
        try:
            from waooaw.vision.vision_stack import VisionStack

            self.vision_stack = VisionStack(self.db)
        except Exception as e:
            logger.warning(f"VisionStack not available: {e}")
            self.vision_stack = None

        # Vision-specific state
        self.core_identity: Dict[str, Any] = {}
        self.policies: Dict[str, Any] = {}
        self.current_phase: str = "phase1_foundation"

    # =====================================
    # OVERRIDE: SPECIALIZATION
    # =====================================

    def _load_specialization(self) -> AgentSpecialization:
        """Load WowVision Prime specialization"""
        return AgentSpecialization(
            coe_name="WowVision Prime",
            coe_type="vision_guardian",
            domain="Vision Enforcement",
            expertise="3-layer vision stack validation",
            version="1.0.0",
            core_responsibilities=[
                "Validate all file creations against vision",
                "Review PRs for vision compliance",
                "Process human escalations",
                "Manage Layer 2 policies autonomously",
                "Learn vision violation patterns",
            ],
            capabilities={
                "technical": [
                    "Deterministic vision rule validation",
                    "LLM-powered ambiguity resolution",
                    "Pattern recognition for violations",
                    "GitHub issue creation and management",
                ],
                "business": [
                    "Brand consistency enforcement",
                    "Vision alignment validation",
                    "Policy interpretation and application",
                ],
            },
            constraints=[
                {
                    "rule": "NEVER generate Python code in Phase 1",
                    "reason": "Foundation phase focuses on architecture",
                },
                {
                    "rule": "Always escalate Layer 1 violations to human",
                    "reason": "Core vision changes require human approval",
                },
                {
                    "rule": "Cannot modify vision stack Layer 1",
                    "reason": "Layer 1 is immutable foundation",
                },
            ],
            skill_requirements=[
                "Vision stack comprehension (Layers 1-3)",
                "YAML/JSON parsing and validation",
                "GitHub API integration",
                "Brand consistency evaluation",
            ],
        )

    # =====================================
    # OVERRIDE: IDENTITY
    # =====================================(keeping for backward compatibility during transition) # noqa: E501

    def _restore_identity(self) -> None:
        """Load WowVision identity from vision stack"""
        try:
            if self.vision_stack:
                self.core_identity = self.vision_stack.get_core()
                self.policies = self.vision_stack.get_policies()
            else:
                # Fallback: Load from context
                self.core_identity = self.context.get(
                    "core_identity",
                    {
                        "role": "Vision Guardian",
                        "responsibilities": [
                            "Validate file creations",
                            "Review PR compliance",
                            "Process escalations",
                        ],
                        "constraints": [
                            "NEVER generate Python code in Phase 1",
                            "Always validate against vision stack",
                        ],
                    },
                )
                self.policies = self.context.get("policies", {})

            self.current_phase = self._get_current_phase()

            logger.info(f"✅ Identity: WowVision Prime - Phase {self.current_phase}")

        except Exception as e:
            logger.error(f"Failed to restore identity: {e}")
            # Set minimal identity
            self.core_identity = {"role": "Vision Guardian"}
            self.policies = {}

    # =====================================
    # OVERRIDE: DETERMINISTIC DECISIONS
    # =====================================

    def should_wake(self, event: Dict[str, Any]) -> bool:
        """
        WowVision Prime wake filter - only wake for relevant events.
        
        Wake for:
        - File creations (need to validate against vision)
        - PR opened (need to review for vision compliance)
        - Issue comments (human escalation responses)
        
        Skip:
        - README.md edits (documentation, not code)
        - Config file changes (.yaml, .json, etc.)
        - Bot commits (automated, pre-approved)
        - File deletions (can't violate vision by deleting)
        - Branch operations (not file-level validation)
        
        Args:
            event: Event dict with event_type and payload
            
        Returns:
            bool: True if agent should wake
        """
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        
        # ===== WAKE CONDITIONS =====
        
        # Wake on: File created
        if event_type == EVENT_FILE_CREATED:
            file_path = payload.get("file_path", "")
            
            # Skip: README.md (documentation)
            if file_path.lower() == "readme.md" or file_path.lower().endswith("/readme.md"):
                logger.debug(f"{self.agent_id}: Skip README.md edit")
                return False
            
            # Skip: Config files (.yaml, .json, .toml, .env)
            config_exts = [".yaml", ".yml", ".json", ".toml", ".ini", ".env", ".env.example"]
            if any(file_path.endswith(ext) for ext in config_exts):
                logger.debug(f"{self.agent_id}: Skip config file {file_path}")
                return False
            
            # Skip: Lock files (package-lock.json, poetry.lock, etc.)
            if "lock" in file_path.lower():
                logger.debug(f"{self.agent_id}: Skip lock file {file_path}")
                return False
            
            # Wake for all other file creations
            logger.info(f"{self.agent_id}: WAKE for file creation: {file_path}")
            return True
        
        # Wake on: File updated (same rules as created)
        if event_type == EVENT_FILE_UPDATED:
            file_path = payload.get("file_path", "")
            
            # Skip: Same exceptions as file_created
            if file_path.lower() == "readme.md" or file_path.lower().endswith("/readme.md"):
                return False
            config_exts = [".yaml", ".yml", ".json", ".toml", ".ini", ".env", ".env.example"]
            if any(file_path.endswith(ext) for ext in config_exts):
                return False
            if "lock" in file_path.lower():
                return False
            
            logger.info(f"{self.agent_id}: WAKE for file update: {file_path}")
            return True
        
        # Wake on: PR opened (need to review entire PR)
        if event_type == EVENT_PR_OPENED:
            pr_number = payload.get("pr_number", "")
            logger.info(f"{self.agent_id}: WAKE for PR opened: #{pr_number}")
            return True
        
        # Wake on: Issue comment (human escalation response)
        if event_type == EVENT_ISSUE_COMMENT:
            issue_number = payload.get("issue_number", "")
            comment_body = payload.get("comment_body", "")
            
            # Only wake if comment looks like escalation response
            escalation_keywords = ["APPROVE:", "REJECT:", "MODIFY:", "vision-violation"]
            if any(keyword in comment_body for keyword in escalation_keywords):
                logger.info(f"{self.agent_id}: WAKE for escalation response: #{issue_number}")
                return True
            else:
                logger.debug(f"{self.agent_id}: Skip non-escalation comment")
                return False
        
        # Wake on: Commit pushed (might contain file changes)
        if event_type == EVENT_COMMIT_PUSHED:
            commit_sha = payload.get("commit_sha", "")
            author = payload.get("author", "")
            
            # Skip: Bot commits
            bot_keywords = ["bot", "github-actions", "dependabot", "renovate"]
            if any(keyword in author.lower() for keyword in bot_keywords):
                logger.debug(f"{self.agent_id}: Skip bot commit from {author}")
                return False
            
            logger.info(f"{self.agent_id}: WAKE for commit: {commit_sha[:7]} by {author}")
            return True
        
        # ===== SKIP CONDITIONS (explicit) =====
        
        # Skip: File deleted (can't violate vision by deleting)
        if event_type in ["github.file.deleted", "github.pr.closed", "github.branch.deleted"]:
            logger.debug(f"{self.agent_id}: Skip {event_type}")
            return False
        
        # Default: Skip unknown events (conservative approach)
        logger.debug(f"{self.agent_id}: Skip unknown event type: {event_type}")
        return False

    # =====================================
    # DETERMINISTIC DECISION RULES
    # =====================================

    def _try_deterministic_decision(self, request: Dict[str, Any]) -> Decision:
        """Vision-specific deterministic validation"""

        # Rule 1: Check immutable constraints
        for constraint in self.core_identity.get("constraints", []):
            violation = self._violates_constraint(request, constraint)
            if violation:
                return Decision(
                    approved=False,
                    reason=f"Violates core constraint: {constraint}",
                    confidence=1.0,
                    citations=["waooaw-core.yaml#constraints"],
                    method="deterministic",
                )

        # Rule 2: Check phase rules for file creation
        if request.get("type") == "create_file":
            path = request.get("path", "")
            file_ext = f".{path.split('.')[-1]}" if "." in path else ""

            phase_rules = self.policies.get("phase_rules", {}).get(
                self.current_phase, {}
            )

            # Forbidden file types?
            forbidden = phase_rules.get("file_types_forbidden", [])
            if file_ext in forbidden:
                return Decision(
                    approved=False,
                    reason=f"Phase {self.current_phase} forbids {file_ext} files",
                    confidence=1.0,
                    citations=["waooaw-policies.yaml#phase_rules"],
                    method="deterministic",
                )

            # Allowed file types?
            allowed = phase_rules.get("file_types_allowed", [])
            if allowed and file_ext in allowed:
                return Decision(
                    approved=True,
                    reason=f"Phase {self.current_phase} allows {file_ext} files",
                    confidence=1.0,
                    citations=["waooaw-policies.yaml#phase_rules"],
                    method="deterministic",
                )

        # Rule 3: Always allow markdown documentation
        if request.get("type") == "create_file":
            path = request.get("path", "")
            if path.endswith(".md") or path.endswith(".markdown"):
                return Decision(
                    approved=True,
                    reason="Documentation files (.md) are always allowed",
                    confidence=1.0,
                    citations=["waooaw-policies.yaml#documentation"],
                    method="deterministic",
                )

        # Rule 4: Always allow config files
        if request.get("type") == "create_file":
            path = request.get("path", "")
            config_exts = [".yaml", ".yml", ".json", ".toml", ".ini", ".env.example"]
            if any(path.endswith(ext) for ext in config_exts):
                return Decision(
                    approved=True,
                    reason=f"Configuration files are allowed",
                    confidence=1.0,
                    citations=["waooaw-policies.yaml#config"],
                    method="deterministic",
                )

        # Ambiguous - needs LLM
        return Decision(
            approved=False,
            confidence=0.5,
            reason="No deterministic rule applies",
            method="none",
        )

    # =====================================
    # OVERRIDE: TASK EXECUTION
    # =====================================

    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get WowVision-specific tasks"""
        tasks: List[Dict[str, Any]] = []

        try:
            # Task 1: Validate recent file creations
            for commit in self._get_recent_commits(
                since=datetime.now() - timedelta(hours=1)
            ):
                for file in commit.files:
                    if file.status == "added":
                        tasks.append(
                            {
                                "type": "validate_file_creation",
                                "data": {
                                    "file": {
                                        "filename": file.filename,
                                        "status": file.status,
                                        "additions": file.additions,
                                        "deletions": file.deletions,
                                    },
                                    "commit": {
                                        "sha": commit.sha,
                                        "message": commit.commit.message,
                                        "author": commit.commit.author.name,
                                    },
                                },
                            }
                        )

            # Task 2: Review open PRs
            for pr in self._get_open_prs():
                pr_labels = [label.name for label in pr.labels]
                if "vision-validation-needed" in pr_labels:
                    tasks.append(
                        {
                            "type": "validate_pr",
                            "data": {
                                "pr": {
                                    "number": pr.number,
                                    "title": pr.title,
                                    "state": pr.state,
                                    "labels": pr_labels,
                                }
                            },
                        }
                    )

            # Task 3: Process escalation responses
            tasks.extend(self._get_pending_escalations())

        except Exception as e:
            logger.error(f"Failed to get pending tasks: {e}")

        return tasks

    def execute_task(self, task: Dict[str, Any]) -> None:
        """Execute WowVision-specific task"""

        task_type = task.get("type")

        if task_type == "validate_file_creation":
            self._validate_file_creation(task["data"])

        elif task_type == "validate_pr":
            self._validate_pr(task["data"])

        elif task_type == "process_escalation":
            self._process_escalation(task["data"])

        else:
            logger.warning(f"Unknown task type: {task_type}")

    def _validate_file_creation(self, data: Dict[str, Any]) -> None:
        """Validate file creation against vision stack"""
        file_data = data["file"]
        commit_data = data["commit"]

        filename = file_data["filename"]

        # Use base decision framework
        decision = self.make_decision(
            {
                "type": "create_file",
                "path": filename,
                "agent_id": commit_data["author"],
                "commit_sha": commit_data["sha"],
            }
        )

        if not decision.approved:
            # Create escalation issue
            self._escalate_violation(filename, commit_data, decision)
            logger.warning(f"❌ Violation: {filename}")
        else:
            logger.info(f"✅ Validated: {filename} (method={decision.method})")

    def _validate_pr(self, data: Dict[str, Any]) -> None:
        """Validate PR for vision compliance"""
        pr_data = data["pr"]

        logger.info(f"Validating PR #{pr_data['number']}: {pr_data['title']}")

        # TODO: Implement PR validation logic
        # For now, just log
        logger.info(f"PR validation not yet implemented for #{pr_data['number']}")

    def _process_escalation(self, data: Dict[str, Any]) -> None:
        """Process escalation response from human"""
        escalation_data = data["escalation"]

        logger.info(f"Processing escalation #{escalation_data.get('id', 'unknown')}")

        # TODO: Implement escalation processing
        # Read GitHub issue comments
        # Update decision based on human feedback
        # Learn from the resolution

    def _escalate_violation(
        self, filename: str, commit: Dict[str, Any], decision: Decision
    ) -> None:
        """Create escalation issue for vision violation"""
        try:
            title = f"🚨 Vision Violation: {filename}"

            body = f"""## Vision Violation Detected

**File**: `{filename}`
**Commit**: {commit['sha'][:7]}
**Author**: {commit['author']}

### Violation Reason
{decision.reason}

### Decision Details
- **Confidence**: {decision.confidence:.2f}
- **Method**: {decision.method}
- **Citations**: {', '.join(decision.citations) if decision.citations else 'None'}

### Context
```
Commit message: {commit['message']}
```

### Required Action
Please review this file creation:
- **APPROVE**: File is acceptable, update vision rules if needed
- **REJECT**: File violates vision, should be removed
- **MODIFY**: File needs changes to comply

Reply with your decision and I will learn from it.

---
*Escalated by WowVision Prime at {datetime.now().isoformat()}*
"""

            labels = ["vision-violation", "wowvision-escalation", "needs-review"]

            issue = self.create_github_issue(title, body, labels)

            # Log escalation in database
            self._log_escalation(filename, commit, decision, issue.number)

        except Exception as e:
            logger.error(f"Failed to escalate violation: {e}")

    def _log_escalation(
        self,
        filename: str,
        commit: Dict[str, Any],
        decision: Decision,
        issue_number: int,
    ) -> None:
        """Log escalation to database"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO human_escalations (
                    agent_id, escalation_reason, action_data,
                    github_issue_number, status, urgency
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    commit["author"],
                    decision.reason,
                    json.dumps(
                        {
                            "filename": filename,
                            "commit": commit,
                            "decision": {
                                "approved": decision.approved,
                                "reason": decision.reason,
                                "confidence": decision.confidence,
                                "method": decision.method,
                            },
                        }
                    ),
                    issue_number,
                    "pending",
                    "medium",
                ),
            )

            self.db.commit()
            cursor.close()

        except Exception as e:
            logger.error(f"Failed to log escalation: {e}")
            self.db.rollback()

    def _get_pending_escalations(self) -> List[Dict[str, Any]]:
        """Get pending escalations awaiting human response"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT * FROM human_escalations
                WHERE status = 'pending'
                AND created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 10
            """
            )

            escalations = cursor.fetchall()
            cursor.close()

            return [
                {
                    "type": "process_escalation",
                    "data": {
                        "escalation": {
                            "id": row[0],
                            "agent_id": row[1],
                            "reason": row[2],
                            "issue_number": row[4],
                        }
                    },
                }
                for row in escalations
            ]

        except Exception as e:
            logger.debug(f"Could not get pending escalations: {e}")
            return []

    # =====================================
    # WOWVISION-SPECIFIC HELPERS
    # =====================================

    def _get_current_phase(self) -> str:
        """Get current platform phase"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT state_value FROM wowvision_state
                WHERE state_key = 'current_phase'
            """
            )

            result = cursor.fetchone()
            cursor.close()

            if result:
                state_value = (
                    json.loads(result[0]) if isinstance(result[0], str) else result[0]
                )
                return state_value.get("phase", "phase1_foundation")

        except Exception as e:
            logger.debug(f"Could not get current phase: {e}")

        return "phase1_foundation"

    def _violates_constraint(self, request: Dict[str, Any], constraint: str) -> bool:
        """Check if request violates core constraint"""

        # Constraint: "NEVER generate Python code in Phase 1"
        if "NEVER generate Python code in Phase 1" in constraint:
            if (
                self.current_phase.startswith("phase1")
                and request.get("type") == "create_file"
                and request.get("path", "").endswith(".py")
            ):
                # Exception: waooaw/ directory is part of the agent system
                if request.get("path", "").startswith("waooaw/"):
                    return False  # Allowed: agent system code
                return True

        return False

    # =====================================
    # OVERRIDE: LEARNING
    # =====================================

    def _apply_learnings(self, learnings: List[Dict[str, Any]]) -> None:
        """Apply vision-specific learnings"""
        for learning in learnings:
            category = learning.get("category", "")
            title = learning.get("title", "")

            if category.startswith("WowVision-Prime-"):
                logger.debug(f"💡 Applying learning: {title}")

                # Parse learning content (JSONB returns dict, not string)
                try:
                    content = learning.get("content", {})
                    if isinstance(content, str):
                        content = json.loads(content)

                    # Update policies if learning suggests it
                    if "policy_update" in content:
                        self._update_policy(content["policy_update"])

                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Could not parse learning content: {title} - {e}")

    def _update_policy(self, policy_update: Dict[str, Any]) -> None:
        """Update vision policies based on learning"""
        logger.info(f"Updating policy: {policy_update.get('rule', 'unknown')}")
        # TODO: Implement policy update logic

    # =====================================
    # HUMAN RESPONSE PROCESSING
    # =====================================

    def process_human_response(self, issue_number: int, comment_body: str):
        """Process human response to escalation issue"""

        # Parse response
        response = comment_body.strip().upper()

        if "APPROVE" in response:
            decision = "APPROVED"
            self._log_decision(f"Issue #{issue_number}", decision, "Human override")

            # Close issue
            self.comment_on_issue(
                issue_number=issue_number,
                comment=(
                    "✅ **APPROVED by @dlai-sd**\n\n"
                    "Decision recorded. Closing issue."
                ),
            )
            repo = self.github.get_repo(self.config["github_repo"])
            issue = repo.get_issue(issue_number)
            issue.edit(state="closed")

            logger.info(f"✅ Approved issue #{issue_number}")

        elif "REJECT" in response:
            decision = "REJECTED"
            self._log_decision(f"Issue #{issue_number}", decision, "Human enforcement")

            # Add comment and close
            self.comment_on_issue(
                issue_number=issue_number,
                comment=(
                    "❌ **REJECTED by @dlai-sd**\n\n"
                    "Vision rule will be enforced. Closing issue."
                ),
            )

            repo = self.github.get_repo(self.config["github_repo"])
            issue = repo.get_issue(issue_number)
            issue.edit(state="closed")

            logger.info(f"❌ Rejected issue #{issue_number}")

        else:
            logger.warning(
                f"⚠️ Unrecognized response on issue #{issue_number}: {response}"
            )
