"""
Unit Tests for Reflection Engine - Story 4.2
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.reflection_engine import (
    ReflectionEngine,
    OutcomeType,
    Action,
    Reflection
)


class TestReflectionEngine:
    """Test reflection engine."""
    
    def test_init(self):
        """Should initialize engine."""
        engine = ReflectionEngine()
        
        assert len(engine.actions_log) == 0
        assert len(engine.reflections) == 0
    
    def test_log_action(self):
        """Should log actions."""
        engine = ReflectionEngine()
        
        action = engine.log_action(
            action_id="action_1",
            action_type="pr_review",
            input_data={"pr_number": 42},
            output_data={"approved": True},
            outcome=OutcomeType.SUCCESS
        )
        
        assert action.action_id == "action_1"
        assert action.action_type == "pr_review"
        assert action.outcome == OutcomeType.SUCCESS
        assert len(engine.actions_log) == 1
    
    def test_reflect_on_success(self):
        """Should reflect on successful action."""
        engine = ReflectionEngine()
        
        engine.log_action(
            action_id="success_1",
            action_type="pr_review",
            input_data={},
            output_data={"approved": True, "violations_found": 0},
            outcome=OutcomeType.SUCCESS
        )
        
        reflection = engine.reflect("success_1")
        
        assert reflection.action_id == "success_1"
        assert len(reflection.what_worked) > 0
        assert reflection.confidence_score > 0
    
    def test_reflect_on_failure(self):
        """Should reflect on failed action."""
        engine = ReflectionEngine()
        
        engine.log_action(
            action_id="failure_1",
            action_type="pr_review",
            input_data={},
            output_data={"false_positive": True},
            outcome=OutcomeType.FAILURE
        )
        
        reflection = engine.reflect("failure_1")
        
        assert len(reflection.what_failed) > 0
        assert len(reflection.improvement_suggestions) > 0
    
    def test_lessons_learned(self):
        """Should extract lessons from actions."""
        engine = ReflectionEngine()
        
        engine.log_action(
            action_id="lesson_1",
            action_type="pr_review",
            input_data={},
            output_data={"approved": True},
            outcome=OutcomeType.SUCCESS,
            metadata={"used_deterministic_rules": True}
        )
        
        reflection = engine.reflect("lesson_1")
        
        assert len(reflection.lessons_learned) > 0
    
    def test_reflect_on_recent(self):
        """Should reflect on multiple recent actions."""
        engine = ReflectionEngine()
        
        # Log multiple actions
        for i in range(5):
            engine.log_action(
                action_id=f"action_{i}",
                action_type="pr_review",
                input_data={},
                output_data={},
                outcome=OutcomeType.SUCCESS
            )
        
        reflections = engine.reflect_on_recent(count=3)
        
        assert len(reflections) <= 3
    
    def test_success_patterns(self):
        """Should track success patterns."""
        engine = ReflectionEngine()
        
        # Log successful actions
        for i in range(3):
            engine.log_action(
                action_id=f"success_{i}",
                action_type="pr_review",
                input_data={},
                output_data={"approved": True},
                outcome=OutcomeType.SUCCESS
            )
            engine.reflect(f"success_{i}")
        
        patterns = engine.get_success_patterns()
        
        assert len(patterns) > 0
        assert patterns[0][1] > 0  # Count > 0
    
    def test_failure_patterns(self):
        """Should track failure patterns."""
        engine = ReflectionEngine()
        
        # Log failed actions
        for i in range(2):
            engine.log_action(
                action_id=f"failure_{i}",
                action_type="pr_review",
                input_data={},
                output_data={"false_positive": True},
                outcome=OutcomeType.FAILURE
            )
            engine.reflect(f"failure_{i}")
        
        patterns = engine.get_failure_patterns()
        
        assert len(patterns) > 0
    
    def test_get_lessons_by_type(self):
        """Should get lessons filtered by action type."""
        engine = ReflectionEngine()
        
        engine.log_action(
            action_id="pr_1",
            action_type="pr_review",
            input_data={},
            output_data={"approved": True},
            outcome=OutcomeType.SUCCESS,
            metadata={"used_llm": True}
        )
        engine.reflect("pr_1")
        
        engine.log_action(
            action_id="decision_1",
            action_type="decision",
            input_data={},
            output_data={},
            outcome=OutcomeType.SUCCESS
        )
        engine.reflect("decision_1")
        
        pr_lessons = engine.get_lessons_by_type("pr_review")
        
        # Should have lessons from PR review only
        assert isinstance(pr_lessons, list)
    
    def test_stats(self):
        """Should report statistics."""
        engine = ReflectionEngine()
        
        engine.log_action("s1", "pr_review", {}, {}, OutcomeType.SUCCESS)
        engine.log_action("f1", "pr_review", {}, {}, OutcomeType.FAILURE)
        engine.reflect("s1")
        
        stats = engine.get_stats()
        
        assert stats["total_actions"] == 2
        assert stats["successes"] == 1
        assert stats["failures"] == 1
        assert stats["success_rate"] == 50.0
        assert stats["reflections_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
