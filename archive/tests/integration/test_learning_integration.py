"""
Integration Tests - Memory + Reflection + Feedback

Tests the integration of learning components.
"""
import pytest
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.memory_system import MemorySystem
from waooaw.learning.reflection_engine import ReflectionEngine, OutcomeType
from waooaw.learning.feedback_loops import FeedbackLoopSystem, FeedbackType, FeedbackSentiment


class TestLearningIntegration:
    """Integration tests for learning components."""
    
    def test_memory_reflection_integration(self):
        """Should integrate memory and reflection."""
        memory = MemorySystem()
        reflection = ReflectionEngine()
        
        # Log an action
        action_id = reflection.log_action(
            action_type="code_review",
            input_data={"pr_number": 123},
            output_data={"approved": True}
        )
        
        # Reflect on it
        result = reflection.reflect(
            action_id=action_id,
            outcome=OutcomeType.SUCCESS,
            context={"reviewer": "ai_agent"}
        )
        
        # Store reflection in memory
        memory_id = memory.store(
            content=f"Reflection: {result.what_worked}",
            memory_type="episodic",
            importance=0.8
        )
        
        # Should have stored
        assert memory_id is not None
        
        # Should be retrievable
        memories = memory.retrieve("code review success")
        assert len(memories) > 0
    
    def test_reflection_feedback_integration(self):
        """Should integrate reflection and feedback loops."""
        reflection = ReflectionEngine()
        feedback_system = FeedbackLoopSystem()
        
        # Log action
        action_id = reflection.log_action(
            action_type="pr_review",
            input_data={"pr": 123},
            output_data={"comments": 5}
        )
        
        # Get feedback
        feedback_id = feedback_system.submit_feedback(
            action_id=action_id,
            feedback_type=FeedbackType.HUMAN,
            sentiment=FeedbackSentiment.POSITIVE,
            content="Great review, very thorough",
            rating=5.0
        )
        
        # Reflect on success
        result = reflection.reflect(
            action_id=action_id,
            outcome=OutcomeType.SUCCESS,
            context={"feedback_received": True}
        )
        
        # Should have learned
        assert len(result.lessons_learned) > 0
        
        # Should have success patterns
        patterns = reflection.get_success_patterns()
        assert len(patterns) > 0
    
    def test_full_learning_cycle(self):
        """Should complete full learning cycle."""
        memory = MemorySystem()
        reflection = ReflectionEngine()
        feedback_system = FeedbackLoopSystem()
        
        # 1. Agent performs action
        action_id = reflection.log_action(
            action_type="bug_fix",
            input_data={"bug_id": 456},
            output_data={"fixed": True, "files_changed": 3}
        )
        
        # 2. Receive feedback
        feedback_system.submit_feedback(
            action_id=action_id,
            feedback_type=FeedbackType.AUTOMATED,
            sentiment=FeedbackSentiment.POSITIVE,
            content="Tests passing",
            rating=5.0
        )
        
        # 3. Reflect on action
        reflection_result = reflection.reflect(
            action_id=action_id,
            outcome=OutcomeType.SUCCESS,
            context={"tests_passed": True}
        )
        
        # 4. Store lessons in memory
        for lesson in reflection_result.lessons_learned:
            memory.store(
                content=lesson,
                memory_type="procedural",
                importance=0.9
            )
        
        # 5. Retrieve similar experiences
        similar = memory.retrieve("bug fix success", top_k=5)
        
        # Should have complete learning cycle
        assert len(similar) > 0
        assert reflection.total_actions > 0
        assert feedback_system.total_feedback_received > 0
    
    def test_improvement_suggestions_flow(self):
        """Should generate and apply improvement suggestions."""
        reflection = ReflectionEngine()
        feedback_system = FeedbackLoopSystem()
        
        # Multiple failed actions
        for i in range(3):
            action_id = reflection.log_action(
                action_type="test_run",
                input_data={"test_suite": f"suite_{i}"},
                output_data={"passed": False}
            )
            
            # Negative feedback
            feedback_system.submit_feedback(
                action_id=action_id,
                feedback_type=FeedbackType.AUTOMATED,
                sentiment=FeedbackSentiment.NEGATIVE,
                content="Tests failed due to timeout",
                rating=1.0
            )
            
            # Reflect on failure
            reflection.reflect(
                action_id=action_id,
                outcome=OutcomeType.FAILURE,
                context={"reason": "timeout"}
            )
        
        # Should have failure patterns
        failures = reflection.get_failure_patterns()
        assert len(failures) > 0
        
        # Should have improvement suggestions from recent reflections
        recent = reflection.reflect_on_recent(count=3)
        
        improvement_count = sum(
            len(r.improvement_suggestions) for r in recent
        )
        
        assert improvement_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
