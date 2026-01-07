"""
E2E Test Scenarios - Complete Agent Workflow

Tests end-to-end agent behavior from wake to completion.
"""
import pytest
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.memory_system import MemorySystem
from waooaw.learning.reflection_engine import ReflectionEngine, OutcomeType
from waooaw.learning.feedback_loops import FeedbackLoopSystem, FeedbackType, FeedbackSentiment
from waooaw.common.logging_framework import get_logger, configure_logging
from waooaw.common.metrics import MetricsCollector


class TestAgentWorkflowE2E:
    """End-to-end tests for complete agent workflows."""
    
    def setup_method(self):
        """Set up for each test."""
        configure_logging(level="INFO", format="json")
        self.logger = get_logger("e2e_test")
        
        # Initialize agent components
        self.memory = MemorySystem()
        self.reflection = ReflectionEngine()
        self.feedback = FeedbackLoopSystem()
        self.metrics = MetricsCollector()
    
    def test_complete_task_execution_workflow(self):
        """E2E: Agent receives task, executes, reflects, learns."""
        # Track metrics
        tasks_counter = self.metrics.counter("tasks_completed", "Tasks completed")
        
        # Agent receives and executes task
        task = {"type": "code_review", "pr_number": 123}
        
        action_id = self.reflection.log_action(
            action_type="code_review",
            input_data=task,
            output_data={"approved": True, "comments": 3}
        )
        
        # Receive feedback
        self.feedback.submit_feedback(
            action_id=action_id,
            feedback_type=FeedbackType.HUMAN,
            sentiment=FeedbackSentiment.POSITIVE,
            content="Great review",
            rating=5.0
        )
        
        # Reflect and learn
        reflection_result = self.reflection.reflect(
            action_id=action_id,
            outcome=OutcomeType.SUCCESS,
            context={}
        )
        
        # Store lessons
        for lesson in reflection_result.lessons_learned:
            self.memory.store(content=lesson, memory_type="procedural", importance=0.9)
        
        tasks_counter.inc()
        
        # Verify workflow
        assert action_id is not None
        assert tasks_counter.get() == 1.0
        assert len(reflection_result.lessons_learned) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
