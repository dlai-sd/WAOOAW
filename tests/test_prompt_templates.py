"""
Unit Tests for Prompt Templates - Story 3.3
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.llm.prompt_templates import PromptTemplates


class TestPromptTemplates:
    """Test prompt templates."""
    
    def test_vision_validation_prompt(self):
        """Should generate vision validation prompt."""
        prompt = PromptTemplates.vision_validation_prompt(
            change_description="Adding new feature X",
            files_changed=["src/feature.py", "tests/test_feature.py"],
            vision_context="Feature X aligns with goal Y"
        )
        
        assert "Vision Validation" in prompt
        assert "Adding new feature X" in prompt
        assert "src/feature.py" in prompt
        assert "Feature X aligns" in prompt
        assert "Alignment Score" in prompt
    
    def test_code_review_prompt(self):
        """Should generate code review prompt."""
        prompt = PromptTemplates.code_review_prompt(
            file_path="src/auth.py",
            file_content="def login(user, password):\n    return True",
            diff="+ def login(user, password):\n+ return True"
        )
        
        assert "Code Review" in prompt
        assert "src/auth.py" in prompt
        assert "def login" in prompt
        assert "Overall Quality" in prompt
    
    def test_code_review_with_focus_areas(self):
        """Should include focus areas in prompt."""
        prompt = PromptTemplates.code_review_prompt(
            file_path="src/api.py",
            file_content="# API code",
            focus_areas=["security", "performance"]
        )
        
        assert "Focus Areas" in prompt
        assert "security" in prompt
        assert "performance" in prompt
    
    def test_ambiguity_resolution_prompt(self):
        """Should generate ambiguity resolution prompt."""
        prompt = PromptTemplates.ambiguity_resolution_prompt(
            ambiguous_situation="Unclear if feature should be admin-only",
            context={"feature": "bulk delete", "impact": "high"},
            options=["Admin only", "All users", "Configurable"]
        )
        
        assert "Ambiguity Resolution" in prompt
        assert "admin-only" in prompt
        assert "1. Admin only" in prompt
        assert "2. All users" in prompt
        assert "Recommended Option" in prompt
    
    def test_pr_approval_decision_prompt(self):
        """Should generate PR approval prompt."""
        violations = [
            {"severity": "critical", "file_path": "src/auth.py", "description": "SQL injection"},
            {"severity": "low", "file_path": "src/utils.py", "description": "Long line"}
        ]
        
        prompt = PromptTemplates.pr_approval_decision_prompt(
            pr_number=42,
            files_count=5,
            violations=violations
        )
        
        assert "PR #42" in prompt
        assert "Files Changed: 5" in prompt
        assert "Critical: 1" in prompt
        assert "Low: 1" in prompt
        assert "SQL injection" in prompt
    
    def test_pr_approval_with_test_results(self):
        """Should include test results in prompt."""
        prompt = PromptTemplates.pr_approval_decision_prompt(
            pr_number=10,
            files_count=3,
            violations=[],
            test_results={"passed": 50, "failed": 2, "coverage": 85}
        )
        
        assert "Test Results" in prompt
        assert "Passed: 50" in prompt
        assert "Failed: 2" in prompt
        assert "Coverage: 85%" in prompt
    
    def test_escalation_prompt(self):
        """Should generate escalation prompt."""
        prompt = PromptTemplates.escalation_prompt(
            trigger="Ambiguous architecture decision",
            reason="Multiple valid approaches with different tradeoffs",
            context={"pr": 42, "options": 3},
            attempted_actions=["Analyzed pros/cons", "Consulted docs", "Reviewed similar cases"]
        )
        
        assert "Escalation Required" in prompt
        assert "Ambiguous architecture" in prompt
        assert "1. Analyzed pros/cons" in prompt
        assert "Urgency" in prompt
    
    def test_system_prompts_exist(self):
        """Should have system prompts defined."""
        assert PromptTemplates.VISION_GUARDIAN_SYSTEM
        assert "WowVision Prime" in PromptTemplates.VISION_GUARDIAN_SYSTEM
        
        assert PromptTemplates.CODE_REVIEWER_SYSTEM
        assert "code review" in PromptTemplates.CODE_REVIEWER_SYSTEM.lower()
        
        assert PromptTemplates.DECISION_MAKER_SYSTEM
        assert "decision" in PromptTemplates.DECISION_MAKER_SYSTEM.lower()
    
    def test_few_shot_examples(self):
        """Should have few-shot examples."""
        assert PromptTemplates.VISION_VALIDATION_EXAMPLES
        assert len(PromptTemplates.VISION_VALIDATION_EXAMPLES) > 0
        
        example = PromptTemplates.VISION_VALIDATION_EXAMPLES[0]
        assert "input" in example
        assert "output" in example


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
