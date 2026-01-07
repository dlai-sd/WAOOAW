"""
Feedback Loop System - Story 4.3

Mechanisms for agents to receive and learn from feedback.
Part of Epic 4: Learning & Memory.
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback."""
    HUMAN = "human"  # From humans
    AUTOMATED = "automated"  # From tests/metrics
    PEER = "peer"  # From other agents
    SELF = "self"  # From self-reflection


class FeedbackSentiment(Enum):
    """Feedback sentiment."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class Feedback:
    """Feedback on an agent action."""
    feedback_id: str
    action_id: str
    feedback_type: FeedbackType
    sentiment: FeedbackSentiment
    content: str
    rating: Optional[float] = None  # 0-5 stars
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class FeedbackAggregation:
    """Aggregated feedback statistics."""
    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_rating: float
    common_themes: List[str]


class FeedbackLoopSystem:
    """
    System for collecting, processing, and learning from feedback.
    
    Features:
    - Collect feedback from multiple sources
    - Aggregate feedback by action/agent
    - Extract actionable insights
    - Update agent behavior based on feedback
    - Track improvement over time
    """
    
    def __init__(self):
        """Initialize feedback loop system."""
        self.feedback_log: List[Feedback] = []
        self.feedback_by_action: Dict[str, List[Feedback]] = {}
        
        # Improvement callbacks
        self.improvement_callbacks: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.total_feedback_received = 0
        self.improvements_applied = 0
        
        logger.info("FeedbackLoopSystem initialized")
    
    def submit_feedback(
        self,
        action_id: str,
        feedback_type: FeedbackType,
        sentiment: FeedbackSentiment,
        content: str,
        rating: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit feedback on an action.
        
        Args:
            action_id: ID of action being evaluated
            feedback_type: Type of feedback source
            sentiment: Positive/negative/neutral
            content: Feedback text
            rating: Optional rating (0-5)
            metadata: Additional context
            
        Returns:
            Feedback ID
        """
        feedback_id = f"fb_{int(time.time() * 1000)}_{self.total_feedback_received}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            action_id=action_id,
            feedback_type=feedback_type,
            sentiment=sentiment,
            content=content,
            rating=rating,
            metadata=metadata or {}
        )
        
        # Store feedback
        self.feedback_log.append(feedback)
        
        if action_id not in self.feedback_by_action:
            self.feedback_by_action[action_id] = []
        self.feedback_by_action[action_id].append(feedback)
        
        self.total_feedback_received += 1
        
        logger.info(
            f"Feedback received: {feedback_id} (action={action_id}, "
            f"type={feedback_type.value}, sentiment={sentiment.value})"
        )
        
        # Process feedback immediately
        self._process_feedback(feedback)
        
        return feedback_id
    
    def get_feedback_for_action(self, action_id: str) -> List[Feedback]:
        """Get all feedback for a specific action."""
        return self.feedback_by_action.get(action_id, [])
    
    def aggregate_feedback(
        self,
        action_id: Optional[str] = None,
        time_window: Optional[float] = None
    ) -> FeedbackAggregation:
        """
        Aggregate feedback statistics.
        
        Args:
            action_id: Filter by action (None = all actions)
            time_window: Only include feedback from last N seconds
            
        Returns:
            Aggregated feedback stats
        """
        # Filter feedback
        if action_id:
            feedback_list = self.get_feedback_for_action(action_id)
        else:
            feedback_list = self.feedback_log
        
        # Apply time window
        if time_window:
            cutoff = time.time() - time_window
            feedback_list = [f for f in feedback_list if f.timestamp >= cutoff]
        
        # Aggregate
        total = len(feedback_list)
        positive = sum(1 for f in feedback_list if f.sentiment == FeedbackSentiment.POSITIVE)
        negative = sum(1 for f in feedback_list if f.sentiment == FeedbackSentiment.NEGATIVE)
        neutral = sum(1 for f in feedback_list if f.sentiment == FeedbackSentiment.NEUTRAL)
        
        # Average rating
        ratings = [f.rating for f in feedback_list if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Extract common themes (simple keyword extraction)
        themes = self._extract_themes(feedback_list)
        
        return FeedbackAggregation(
            total_feedback=total,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            average_rating=avg_rating,
            common_themes=themes
        )
    
    def register_improvement_callback(
        self,
        feedback_pattern: str,
        callback: Callable[[Feedback], None]
    ) -> None:
        """
        Register callback to be triggered on specific feedback patterns.
        
        Args:
            feedback_pattern: Pattern to match (e.g., "false_positive")
            callback: Function to call when pattern matches
        """
        if feedback_pattern not in self.improvement_callbacks:
            self.improvement_callbacks[feedback_pattern] = []
        
        self.improvement_callbacks[feedback_pattern].append(callback)
        
        logger.debug(f"Registered improvement callback for: {feedback_pattern}")
    
    def apply_improvements(self, feedback: Feedback) -> List[str]:
        """
        Apply improvements based on feedback.
        
        Args:
            feedback: Feedback to process
            
        Returns:
            List of improvements applied
        """
        improvements = []
        
        # Check for negative feedback patterns
        if feedback.sentiment == FeedbackSentiment.NEGATIVE:
            content_lower = feedback.content.lower()
            
            if "false positive" in content_lower:
                improvements.append("Increase detection confidence threshold")
                improvements.append("Add more validation rules")
            
            if "missed" in content_lower or "false negative" in content_lower:
                improvements.append("Broaden detection patterns")
                improvements.append("Reduce threshold for edge cases")
            
            if "slow" in content_lower or "timeout" in content_lower:
                improvements.append("Optimize performance")
                improvements.append("Add caching")
            
            if "unclear" in content_lower or "confusing" in content_lower:
                improvements.append("Improve communication clarity")
                improvements.append("Add more context to responses")
        
        # Check for positive feedback patterns
        if feedback.sentiment == FeedbackSentiment.POSITIVE:
            content_lower = feedback.content.lower()
            
            if "helpful" in content_lower:
                improvements.append("Reinforce current approach")
            
            if "fast" in content_lower or "quick" in content_lower:
                improvements.append("Maintain performance optimizations")
        
        # Trigger registered callbacks
        for pattern, callbacks in self.improvement_callbacks.items():
            if pattern.lower() in feedback.content.lower():
                for callback in callbacks:
                    try:
                        callback(feedback)
                        improvements.append(f"Triggered callback: {pattern}")
                    except Exception as e:
                        logger.error(f"Callback failed: {e}", exc_info=True)
        
        if improvements:
            self.improvements_applied += len(improvements)
            logger.info(
                f"Applied {len(improvements)} improvements from feedback {feedback.feedback_id}"
            )
        
        return improvements
    
    def _process_feedback(self, feedback: Feedback) -> None:
        """Process feedback immediately after receiving."""
        # Apply improvements
        improvements = self.apply_improvements(feedback)
        
        # Log for learning
        if improvements:
            feedback.metadata["improvements_applied"] = improvements
    
    def _extract_themes(self, feedback_list: List[Feedback]) -> List[str]:
        """Extract common themes from feedback."""
        # Simple keyword counting
        keyword_counts: Dict[str, int] = {}
        
        keywords = [
            "false positive", "false negative", "slow", "fast",
            "helpful", "unclear", "accurate", "missed", "wrong"
        ]
        
        for feedback in feedback_list:
            content_lower = feedback.content.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Return top themes
        sorted_themes = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [theme for theme, count in sorted_themes[:5]]
    
    def get_improvement_trend(self, time_window: float = 86400) -> Dict[str, Any]:
        """
        Get improvement trend over time.
        
        Args:
            time_window: Time window in seconds (default: 24h)
            
        Returns:
            Trend data
        """
        cutoff = time.time() - time_window
        recent_feedback = [f for f in self.feedback_log if f.timestamp >= cutoff]
        
        if not recent_feedback:
            return {
                "trend": "insufficient_data",
                "positive_ratio": 0.0,
                "average_rating": 0.0
            }
        
        # Calculate metrics
        positive = sum(1 for f in recent_feedback if f.sentiment == FeedbackSentiment.POSITIVE)
        total = len(recent_feedback)
        positive_ratio = positive / total if total > 0 else 0.0
        
        ratings = [f.rating for f in recent_feedback if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Determine trend
        if positive_ratio >= 0.7 and avg_rating >= 4.0:
            trend = "improving"
        elif positive_ratio <= 0.3 or avg_rating <= 2.0:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "positive_ratio": positive_ratio,
            "average_rating": avg_rating,
            "total_feedback": total
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        return {
            "total_feedback_received": self.total_feedback_received,
            "improvements_applied": self.improvements_applied,
            "actions_with_feedback": len(self.feedback_by_action),
            "registered_callbacks": sum(len(cbs) for cbs in self.improvement_callbacks.values())
        }
