"""
Unit Tests for Feedback Loop System - Story 4.3
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.feedback_loops import (
    FeedbackLoopSystem,
    FeedbackType,
    FeedbackSentiment,
    Feedback
)


class TestFeedbackLoopSystem:
    """Test feedback loop system."""
    
    def test_init(self):
        """Should initialize system."""
        system = FeedbackLoopSystem()
        
        assert system.total_feedback_received == 0
        assert len(system.feedback_log) == 0
    
    def test_submit_feedback(self):
        """Should submit feedback."""
        system = FeedbackLoopSystem()
        
        feedback_id = system.submit_feedback(
            action_id="action_1",
            feedback_type=FeedbackType.HUMAN,
            sentiment=FeedbackSentiment.POSITIVE,
            content="Great job!",
            rating=5.0
        )
        
        assert feedback_id.startswith("fb_")
        assert system.total_feedback_received == 1
    
    def test_get_feedback_for_action(self):
        """Should retrieve feedback by action."""
        system = FeedbackLoopSystem()
        
        system.submit_feedback(
            "action_1", FeedbackType.HUMAN, FeedbackSentiment.POSITIVE, "Good"
        )
        system.submit_feedback(
            "action_1", FeedbackType.AUTOMATED, FeedbackSentiment.POSITIVE, "Pass"
        )
        
        feedback = system.get_feedback_for_action("action_1")
        
        assert len(feedback) == 2
    
    def test_aggregate_feedback(self):
        """Should aggregate feedback statistics."""
        system = FeedbackLoopSystem()
        
        system.submit_feedback("a1", FeedbackType.HUMAN, FeedbackSentiment.POSITIVE, "Good", 5.0)
        system.submit_feedback("a1", FeedbackType.HUMAN, FeedbackSentiment.NEGATIVE, "Bad", 2.0)
        
        agg = system.aggregate_feedback("a1")
        
        assert agg.total_feedback == 2
        assert agg.positive_count == 1
        assert agg.negative_count == 1
        assert agg.average_rating == 3.5
    
    def test_improvement_callbacks(self):
        """Should trigger improvement callbacks."""
        system = FeedbackLoopSystem()
        
        callback_triggered = []
        
        def callback(feedback):
            callback_triggered.append(feedback.feedback_id)
        
        system.register_improvement_callback("false positive", callback)
        
        system.submit_feedback(
            "a1",
            FeedbackType.HUMAN,
            FeedbackSentiment.NEGATIVE,
            "This is a false positive"
        )
        
        assert len(callback_triggered) == 1
    
    def test_apply_improvements(self):
        """Should extract improvements from feedback."""
        system = FeedbackLoopSystem()
        
        feedback = Feedback(
            feedback_id="fb_1",
            action_id="a1",
            feedback_type=FeedbackType.HUMAN,
            sentiment=FeedbackSentiment.NEGATIVE,
            content="Too many false positives detected"
        )
        
        improvements = system.apply_improvements(feedback)
        
        assert len(improvements) > 0
        assert any("confidence" in i.lower() for i in improvements)
    
    def test_theme_extraction(self):
        """Should extract common themes."""
        system = FeedbackLoopSystem()
        
        system.submit_feedback("a1", FeedbackType.HUMAN, FeedbackSentiment.NEGATIVE, "False positive issue")
        system.submit_feedback("a2", FeedbackType.HUMAN, FeedbackSentiment.NEGATIVE, "Another false positive")
        system.submit_feedback("a3", FeedbackType.HUMAN, FeedbackSentiment.POSITIVE, "Very helpful")
        
        agg = system.aggregate_feedback()
        
        assert len(agg.common_themes) > 0
        assert "false positive" in agg.common_themes
    
    def test_improvement_trend(self):
        """Should calculate improvement trend."""
        system = FeedbackLoopSystem()
        
        # Add positive feedback
        for i in range(7):
            system.submit_feedback(
                f"a{i}",
                FeedbackType.AUTOMATED,
                FeedbackSentiment.POSITIVE,
                "Pass",
                rating=4.5
            )
        
        # Add some negative
        for i in range(3):
            system.submit_feedback(
                f"an{i}",
                FeedbackType.AUTOMATED,
                FeedbackSentiment.NEGATIVE,
                "Fail",
                rating=2.0
            )
        
        trend = system.get_improvement_trend()
        
        assert trend["trend"] in ["improving", "stable", "declining"]
        assert 0 <= trend["positive_ratio"] <= 1
    
    def test_stats(self):
        """Should report statistics."""
        system = FeedbackLoopSystem()
        
        system.submit_feedback("a1", FeedbackType.HUMAN, FeedbackSentiment.POSITIVE, "Good")
        
        stats = system.get_stats()
        
        assert stats["total_feedback_received"] == 1
        assert stats["actions_with_feedback"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
