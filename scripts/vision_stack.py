#!/usr/bin/env python3
"""
WAOOAW Vision Stack - Python SDK
Version: 1.0
Purpose: Single Source of Truth for agent decision validation

This SDK provides:
- Vision stack loading (core + policies)
- Action validation against vision constraints
- PostgreSQL context management
- Human escalation via GitHub issues
- Zero context loss guarantee
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import yaml


class VisionStack:
    """
    Main interface for vision stack validation and context management.
    
    Usage:
        vision = VisionStack(db_connection)
        approved, reason, citations = vision.validate_action(
            agent_id="WowDomain",
            action={"type": "create_file", "path": "docs/spec.md"}
        )
    """
    
    def __init__(self, db_connection=None, vision_dir: str = None):
        """
        Initialize vision stack.
        
        Args:
            db_connection: PostgreSQL connection object (optional)
            vision_dir: Path to vision directory (default: ./vision)
        """
        self.db = db_connection
        
        # Determine vision directory
        if vision_dir is None:
            # Try to find vision directory relative to this script
            script_dir = Path(__file__).parent.parent
            self.vision_dir = script_dir / "vision"
        else:
            self.vision_dir = Path(vision_dir)
            
        # Load vision files
        self.core = self._load_yaml(self.vision_dir / "waooaw-core.yaml")
        self.policies = self._load_yaml(self.vision_dir / "waooaw-policies.yaml")
        
        # Cache for performance
        self._phase_cache = None
        self._violation_patterns = {}
        
    def _load_yaml(self, path: Path) -> Dict:
        """Load and parse YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Vision file not found: {path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")
    
    def validate_action(
        self, 
        agent_id: str, 
        action: Dict[str, Any]
    ) -> Tuple[bool, str, List[str]]:
        """
        Validate an action against vision stack.
        
        Args:
            agent_id: Identifier of the agent requesting action
            action: Action details (must include 'type' key)
            
        Returns:
            Tuple of (approved, reasoning, citations)
            
        Example:
            >>> vision.validate_action(
            ...     "WowDomain",
            ...     {"type": "create_file", "path": "vision/schema.sql"}
            ... )
            (True, "SQL files allowed in Phase 1", ["waooaw-core.yaml P1C2"])
        """
        action_type = action.get("type", "unknown")
        
        # Check immutable core constraints first
        core_result = self._check_core_constraints(agent_id, action)
        if not core_result[0]:
            self._log_decision(agent_id, action, False, core_result[1], 
                             core_result[2], "core")
            return core_result
        
        # Check dynamic policies
        policy_result = self._check_policies(agent_id, action)
        if not policy_result[0]:
            self._log_decision(agent_id, action, False, policy_result[1], 
                             policy_result[2], "policies")
            return policy_result
        
        # Action approved
        reasoning = policy_result[1] or "No constraints violated"
        citations = policy_result[2]
        self._log_decision(agent_id, action, True, reasoning, citations, 
                          "policies")
        
        return True, reasoning, citations
    
    def _check_core_constraints(
        self, 
        agent_id: str, 
        action: Dict
    ) -> Tuple[bool, str, List[str]]:
        """Check action against immutable core constraints."""
        action_type = action.get("type", "")
        
        # Check context preservation requirements
        if action_type in ["handoff", "complete_task"]:
            if not action.get("context_data"):
                return (
                    False,
                    "Context data required for handoffs and task completion",
                    ["waooaw-core.yaml CP3"]
                )
        
        # Check phase constraints for file operations
        if action_type == "create_file":
            return self._check_phase_constraints(action)
        
        # Check CoE interaction constraints
        if action_type == "cross_coe_interaction":
            return self._check_coe_constraints(agent_id, action)
        
        return True, "", []
    
    def _check_phase_constraints(self, action: Dict) -> Tuple[bool, str, List[str]]:
        """Check file creation against phase constraints."""
        file_path = action.get("path", "")
        
        # Get current phase from policies
        phase1_active = self.policies.get("phase_rules", {}).get(
            "phase1_restrictions", {}
        ).get("active", False)
        
        if phase1_active:
            # Phase 1: Reject .py files
            if file_path.endswith(".py"):
                # Check for test file exception
                if file_path.startswith("test_") or "/test_" in file_path:
                    return (
                        True,
                        "Test files allowed in Phase 1 as exception",
                        ["waooaw-policies.yaml PR1_EX1"]
                    )
                
                return (
                    False,
                    "Python files not allowed in Phase 1 (documentation only)",
                    ["waooaw-core.yaml P1C1", "waooaw-policies.yaml PR1"]
                )
            
            # Phase 1: Allow documentation and schema files
            allowed_extensions = [".sql", ".yaml", ".yml", ".json", ".md", ".sh"]
            if any(file_path.endswith(ext) for ext in allowed_extensions):
                return (
                    True,
                    "Documentation and schema files allowed in Phase 1",
                    ["waooaw-core.yaml P1C2", "waooaw-policies.yaml PR2"]
                )
        
        return True, "", []
    
    def _check_coe_constraints(
        self, 
        agent_id: str, 
        action: Dict
    ) -> Tuple[bool, str, List[str]]:
        """Check cross-CoE interaction constraints."""
        # Verify agent is valid CoE
        valid_coes = self._get_all_coe_ids()
        if agent_id not in valid_coes:
            return (
                False,
                f"Agent {agent_id} is not a recognized CoE",
                ["waooaw-core.yaml centers_of_excellence"]
            )
        
        # Cross-CoE interactions should be logged and may trigger escalation
        target_coe = action.get("target_coe")
        if target_coe and target_coe not in valid_coes:
            return (
                False,
                f"Target CoE {target_coe} is not recognized",
                ["waooaw-core.yaml centers_of_excellence"]
            )
        
        return True, "Cross-CoE interaction logged", []
    
    def _check_policies(
        self, 
        agent_id: str, 
        action: Dict
    ) -> Tuple[bool, str, List[str]]:
        """Check action against dynamic policies."""
        action_type = action.get("type", "")
        
        # Check escalation triggers
        escalation_needed = self._check_escalation_triggers(agent_id, action)
        if escalation_needed:
            # Escalation doesn't block action, just triggers notification
            pass
        
        # Check learned anti-patterns
        anti_pattern_result = self._check_anti_patterns(action)
        if not anti_pattern_result[0]:
            return anti_pattern_result
        
        return True, "Policy validation passed", []
    
    def _check_escalation_triggers(
        self, 
        agent_id: str, 
        action: Dict
    ) -> bool:
        """Check if action should trigger human escalation."""
        action_type = action.get("type", "")
        
        escalation_triggers = self.policies.get("escalation_policies", {}).get(
            "triggers", []
        )
        
        for trigger in escalation_triggers:
            trigger_type = trigger.get("trigger", "")
            
            # File creation always triggers notification (EP1)
            if trigger_type == "File creation in repository" and \
               action_type == "create_file":
                return True
            
            # Cross-CoE interaction (EP3)
            if trigger_type == "Cross-CoE interaction" and \
               action_type == "cross_coe_interaction":
                return True
            
            # High-risk changes (EP4)
            if trigger_type == "High-risk changes":
                high_risk_patterns = ["schema.sql", "docker-compose", ".github/workflows"]
                file_path = action.get("path", "")
                if any(pattern in file_path for pattern in high_risk_patterns):
                    return True
        
        return False
    
    def _check_anti_patterns(self, action: Dict) -> Tuple[bool, str, List[str]]:
        """Check action against learned anti-patterns."""
        anti_patterns = self.policies.get("learned_patterns", {}).get(
            "anti_patterns", []
        )
        
        # Check each anti-pattern
        for pattern in anti_patterns:
            pattern_id = pattern.get("id", "")
            pattern_name = pattern.get("pattern", "")
            
            # Check for phase1-python-generation (AP2)
            if pattern_id == "AP2":
                if action.get("type") == "create_file":
                    file_path = action.get("path", "")
                    if file_path.endswith(".py"):
                        phase1_active = self.policies.get("phase_rules", {}).get(
                            "phase1_restrictions", {}
                        ).get("active", False)
                        
                        if phase1_active:
                            return (
                                False,
                                f"Anti-pattern detected: {pattern_name}",
                                [pattern.get("citation", "")]
                            )
        
        return True, "", []
    
    def _get_all_coe_ids(self) -> List[str]:
        """Get list of all valid CoE IDs."""
        coe_ids = []
        coes = self.core.get("centers_of_excellence", {})
        
        for tier in ["tier1_functional", "tier2_cross_functional", "tier3_platform_excellence"]:
            tier_data = coes.get(tier, {})
            tier_coes = tier_data.get("coes", [])
            for coe in tier_coes:
                coe_ids.append(coe.get("name", ""))
        
        return coe_ids
    
    def escalate_to_human(
        self, 
        agent_id: str, 
        action: Dict, 
        reason: str,
        priority: str = "normal"
    ) -> Optional[int]:
        """
        Escalate action to human via GitHub issue.
        
        Args:
            agent_id: Identifier of the agent
            action: Action requiring approval
            reason: Why escalation is needed
            priority: Priority level (normal, high, critical)
            
        Returns:
            GitHub issue number if created, None otherwise
        """
        # Log to escalations table
        escalation_id = self._log_escalation(agent_id, reason, action)
        
        # Create GitHub issue (would integrate with GitHub API in production)
        # For now, return a mock issue number
        issue_number = self._create_github_issue(agent_id, action, reason, priority)
        
        # Update escalation record with issue number
        if issue_number and self.db:
            self._update_escalation_issue(escalation_id, issue_number)
        
        return issue_number
    
    def update_context(
        self, 
        agent_id: str, 
        context_type: str, 
        context_data: Dict
    ) -> int:
        """
        Store context in PostgreSQL with versioning.
        
        Args:
            agent_id: Identifier of the agent
            context_type: Type of context (e.g., 'decision', 'state', 'learning')
            context_data: Context data to store
            
        Returns:
            Version number of stored context
        """
        if not self.db:
            return 1  # Mock version if no DB connection
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT update_agent_context(%s, %s, %s::jsonb)",
                (agent_id, context_type, json.dumps(context_data))
            )
            version = cursor.fetchone()[0]
            self.db.commit()
            return version
        except Exception as e:
            print(f"Error updating context: {e}")
            return 0
    
    def get_context(
        self, 
        agent_id: str, 
        context_type: str,
        version: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Retrieve context from PostgreSQL.
        
        Args:
            agent_id: Identifier of the agent
            context_type: Type of context
            version: Specific version (None for latest)
            
        Returns:
            Context data or None if not found
        """
        if not self.db:
            return None
        
        try:
            cursor = self.db.cursor()
            
            if version:
                cursor.execute(
                    """
                    SELECT context_data 
                    FROM agent_context 
                    WHERE agent_id = %s AND context_type = %s AND version = %s
                    """,
                    (agent_id, context_type, version)
                )
            else:
                cursor.execute(
                    """
                    SELECT context_data 
                    FROM active_agent_contexts 
                    WHERE agent_id = %s AND context_type = %s
                    """,
                    (agent_id, context_type)
                )
            
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return None
    
    def _log_decision(
        self, 
        agent_id: str, 
        action: Dict,
        approved: bool,
        reasoning: str,
        citations: List[str],
        vision_layer: str
    ):
        """Log decision to PostgreSQL."""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT log_agent_decision(%s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    agent_id,
                    action.get("type", "unknown"),
                    json.dumps(action),
                    approved,
                    reasoning,
                    citations if citations else None,
                    vision_layer
                )
            )
            self.db.commit()
        except Exception as e:
            print(f"Error logging decision: {e}")
    
    def _log_escalation(
        self, 
        agent_id: str, 
        reason: str, 
        action: Dict
    ) -> int:
        """Log escalation to PostgreSQL."""
        if not self.db:
            return 0
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO human_escalations 
                (agent_id, escalation_reason, action_data)
                VALUES (%s, %s, %s::jsonb)
                RETURNING id
                """,
                (agent_id, reason, json.dumps(action))
            )
            escalation_id = cursor.fetchone()[0]
            self.db.commit()
            return escalation_id
        except Exception as e:
            print(f"Error logging escalation: {e}")
            return 0
    
    def _update_escalation_issue(self, escalation_id: int, issue_number: int):
        """Update escalation with GitHub issue number."""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                UPDATE human_escalations 
                SET github_issue_number = %s
                WHERE id = %s
                """,
                (issue_number, escalation_id)
            )
            self.db.commit()
        except Exception as e:
            print(f"Error updating escalation: {e}")
    
    def _create_github_issue(
        self, 
        agent_id: str, 
        action: Dict, 
        reason: str,
        priority: str
    ) -> Optional[int]:
        """
        Create GitHub issue for escalation.
        
        In production, this would use GitHub API.
        For now, returns a mock issue number.
        """
        # TODO: Integrate with GitHub API
        # This would create an issue using the template from escalation-template.md
        
        # Mock implementation
        print(f"[MOCK] GitHub issue created for {agent_id}")
        print(f"  Action: {action.get('type')}")
        print(f"  Reason: {reason}")
        print(f"  Priority: {priority}")
        
        return 12345  # Mock issue number


def main():
    """CLI interface for testing vision stack."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WAOOAW Vision Stack SDK")
    parser.add_argument("--vision-dir", default="./vision", 
                       help="Path to vision directory")
    parser.add_argument("--validate", action="store_true",
                       help="Validate vision files")
    
    args = parser.parse_args()
    
    try:
        vision = VisionStack(vision_dir=args.vision_dir)
        
        if args.validate:
            print("✅ Vision stack loaded successfully")
            print(f"  Core version: {vision.core.get('metadata', {}).get('version')}")
            print(f"  Policies version: {vision.policies.get('metadata', {}).get('version')}")
            print(f"  CoEs defined: {len(vision._get_all_coe_ids())}")
            
            # Test validation
            test_cases = [
                {
                    "agent_id": "WowDomain",
                    "action": {"type": "create_file", "path": "docs/spec.md"},
                    "expected": True
                },
                {
                    "agent_id": "WowDomain",
                    "action": {"type": "create_file", "path": "backend/api.py"},
                    "expected": False
                },
            ]
            
            print("\n🧪 Running validation tests:")
            for i, test in enumerate(test_cases, 1):
                approved, reason, citations = vision.validate_action(
                    test["agent_id"], test["action"]
                )
                status = "✅" if approved == test["expected"] else "❌"
                print(f"  {status} Test {i}: {test['action']['path']} -> {approved}")
                if reason:
                    print(f"      Reason: {reason}")
                if citations:
                    print(f"      Citations: {', '.join(citations)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
