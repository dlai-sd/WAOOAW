"""
Feedback Analysis System

Collects and analyzes user feedback for agent improvement.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict, Counter


class FeedbackType(str, Enum):
    """Type of user feedback"""
    RATING = "rating"  # Star rating (1-5)
    COMMENT = "comment"  # Text feedback
    THUMBS = "thumbs"  # Thumbs up/down
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


@dataclass
class FeedbackEntry:
    """User feedback entry"""
    feedback_id: str
    feedback_type: FeedbackType
    user_id: str
    agent_variant_id: str
    task_id: str
    
    # Feedback content
    rating: Optional[float] = None  # 1-5 stars
    thumbs: Optional[bool] = None  # True=up, False=down
    comment: Optional[str] = None
    
    # Context
    task_description: str = ""
    task_category: Optional[str] = None
    response_quality: Optional[str] = None  # poor, fair, good, excellent
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.value,
            "user_id": self.user_id,
            "agent_variant_id": self.agent_variant_id,
            "task_id": self.task_id,
            "rating": self.rating,
            "thumbs": self.thumbs,
            "comment": self.comment,
            "task_description": self.task_description,
            "task_category": self.task_category,
            "response_quality": self.response_quality,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class FeedbackInsight:
    """Insight derived from feedback analysis"""
    insight_id: str
    category: str  # user_satisfaction, quality_issue, feature_gap, etc.
    description: str
    severity: str  # low, medium, high, critical
    affected_agents: List[str] = field(default_factory=list)
    supporting_feedback: List[str] = field(default_factory=list)  # feedback IDs
    recommendation: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)


class FeedbackAnalyzer:
    """
    Analyzes user feedback to identify improvement areas.
    
    Processes ratings, comments, and reports to generate actionable insights.
    """
    
    def __init__(self):
        """Initialize feedback analyzer"""
        self._feedback: List[FeedbackEntry] = []
        self._insights: List[FeedbackInsight] = []
    
    def collect_feedback(self, feedback: FeedbackEntry):
        """Collect user feedback"""
        self._feedback.append(feedback)
    
    def analyze_feedback(self) -> List[FeedbackInsight]:
        """
        Analyze collected feedback to generate insights.
        
        Returns:
            List of feedback insights
        """
        insights = []
        
        # Analyze ratings
        rating_insights = self._analyze_ratings()
        insights.extend(rating_insights)
        
        # Analyze comments
        comment_insights = self._analyze_comments()
        insights.extend(comment_insights)
        
        # Analyze bug reports
        bug_insights = self._analyze_bug_reports()
        insights.extend(bug_insights)
        
        # Analyze feature requests
        feature_insights = self._analyze_feature_requests()
        insights.extend(feature_insights)
        
        self._insights = insights
        return insights
    
    def _analyze_ratings(self) -> List[FeedbackInsight]:
        """Analyze rating feedback"""
        insights = []
        
        # Get ratings by agent variant
        variant_ratings = defaultdict(list)
        for fb in self._feedback:
            if fb.feedback_type == FeedbackType.RATING and fb.rating is not None:
                variant_ratings[fb.agent_variant_id].append(fb.rating)
        
        # Find low-rated agents
        for variant, ratings in variant_ratings.items():
            if len(ratings) >= 5:  # Need minimum sample size
                avg_rating = sum(ratings) / len(ratings)
                
                if avg_rating < 3.0:  # Low rating
                    insights.append(FeedbackInsight(
                        insight_id=f"rating_low_{variant}",
                        category="user_satisfaction",
                        description=f"Agent variant '{variant}' has low average rating: {avg_rating:.2f}/5.0",
                        severity="high" if avg_rating < 2.5 else "medium",
                        affected_agents=[variant],
                        supporting_feedback=[
                            fb.feedback_id for fb in self._feedback
                            if fb.agent_variant_id == variant and fb.rating is not None and fb.rating < 3.0
                        ],
                        recommendation=f"Review and improve {variant} prompts and capabilities"
                    ))
                elif avg_rating >= 4.5:  # Excellent rating
                    insights.append(FeedbackInsight(
                        insight_id=f"rating_high_{variant}",
                        category="user_satisfaction",
                        description=f"Agent variant '{variant}' has excellent rating: {avg_rating:.2f}/5.0",
                        severity="low",  # This is positive
                        affected_agents=[variant],
                        supporting_feedback=[
                            fb.feedback_id for fb in self._feedback
                            if fb.agent_variant_id == variant and fb.rating is not None and fb.rating >= 4.5
                        ],
                        recommendation=f"Analyze success factors of {variant} for replication"
                    ))
        
        return insights
    
    def _analyze_comments(self) -> List[FeedbackInsight]:
        """Analyze text comments"""
        insights = []
        
        # Get comments
        comments = [fb for fb in self._feedback if fb.comment]
        
        if len(comments) < 3:
            return insights
        
        # Simple sentiment analysis (keyword-based)
        negative_keywords = {
            "bad", "poor", "terrible", "awful", "wrong", "incorrect", "useless",
            "disappointed", "frustrating", "slow", "error", "failed", "broken"
        }
        
        positive_keywords = {
            "good", "great", "excellent", "amazing", "perfect", "helpful",
            "useful", "fast", "accurate", "love", "fantastic", "wonderful"
        }
        
        # Analyze sentiment by agent variant
        variant_sentiment = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
        variant_negative_comments = defaultdict(list)
        variant_positive_comments = defaultdict(list)
        
        for fb in comments:
            comment_lower = fb.comment.lower()
            has_positive = any(kw in comment_lower for kw in positive_keywords)
            has_negative = any(kw in comment_lower for kw in negative_keywords)
            
            if has_negative and not has_positive:
                variant_sentiment[fb.agent_variant_id]["negative"] += 1
                variant_negative_comments[fb.agent_variant_id].append(fb)
            elif has_positive and not has_negative:
                variant_sentiment[fb.agent_variant_id]["positive"] += 1
                variant_positive_comments[fb.agent_variant_id].append(fb)
            else:
                variant_sentiment[fb.agent_variant_id]["neutral"] += 1
        
        # Generate insights for negative sentiment
        for variant, sentiment in variant_sentiment.items():
            total = sentiment["positive"] + sentiment["negative"] + sentiment["neutral"]
            if total >= 3:
                negative_ratio = sentiment["negative"] / total
                
                if negative_ratio >= 0.4:  # 40%+ negative
                    insights.append(FeedbackInsight(
                        insight_id=f"sentiment_negative_{variant}",
                        category="quality_issue",
                        description=f"Agent variant '{variant}' has negative sentiment in {int(negative_ratio * 100)}% of comments",
                        severity="high" if negative_ratio >= 0.6 else "medium",
                        affected_agents=[variant],
                        supporting_feedback=[fb.feedback_id for fb in variant_negative_comments[variant]],
                        recommendation=f"Review negative feedback for {variant} and address common complaints"
                    ))
        
        return insights
    
    def _analyze_bug_reports(self) -> List[FeedbackInsight]:
        """Analyze bug reports"""
        insights = []
        
        # Get bug reports
        bugs = [fb for fb in self._feedback if fb.feedback_type == FeedbackType.BUG_REPORT]
        
        if len(bugs) < 2:
            return insights
        
        # Group by agent variant
        variant_bugs = defaultdict(list)
        for fb in bugs:
            variant_bugs[fb.agent_variant_id].append(fb)
        
        # Generate insights for variants with multiple bugs
        for variant, bug_list in variant_bugs.items():
            if len(bug_list) >= 2:
                insights.append(FeedbackInsight(
                    insight_id=f"bugs_{variant}",
                    category="quality_issue",
                    description=f"Agent variant '{variant}' has {len(bug_list)} reported bugs",
                    severity="critical" if len(bug_list) >= 5 else "high",
                    affected_agents=[variant],
                    supporting_feedback=[fb.feedback_id for fb in bug_list],
                    recommendation=f"Prioritize bug fixes for {variant}"
                ))
        
        return insights
    
    def _analyze_feature_requests(self) -> List[FeedbackInsight]:
        """Analyze feature requests"""
        insights = []
        
        # Get feature requests
        features = [fb for fb in self._feedback if fb.feedback_type == FeedbackType.FEATURE_REQUEST]
        
        if len(features) < 3:
            return insights
        
        # Simple keyword extraction to find common requests
        all_comments = " ".join(fb.comment or "" for fb in features).lower()
        
        # Common feature keywords
        feature_keywords = {
            "export": "data export functionality",
            "template": "template or preset support",
            "integration": "third-party integrations",
            "customization": "customization options",
            "scheduling": "scheduling capabilities",
            "collaboration": "collaboration features",
            "analytics": "analytics and reporting",
            "api": "API access"
        }
        
        # Find requested features
        requested = []
        for keyword, description in feature_keywords.items():
            if keyword in all_comments:
                count = sum(1 for fb in features if keyword in (fb.comment or "").lower())
                if count >= 2:
                    requested.append((description, count))
        
        # Generate insights for top requests
        for description, count in sorted(requested, key=lambda x: x[1], reverse=True)[:3]:
            insights.append(FeedbackInsight(
                insight_id=f"feature_{description.replace(' ', '_')}",
                category="feature_gap",
                description=f"Users requesting: {description} ({count} requests)",
                severity="medium",
                affected_agents=[],  # Applies to platform
                supporting_feedback=[
                    fb.feedback_id for fb in features
                    if any(kw in (fb.comment or "").lower() for kw, desc in feature_keywords.items() if desc == description)
                ],
                recommendation=f"Consider implementing: {description}"
            ))
        
        return insights
    
    def get_agent_satisfaction_score(self, agent_variant_id: str) -> Optional[float]:
        """
        Get satisfaction score for agent variant.
        
        Args:
            agent_variant_id: Agent variant to analyze
            
        Returns:
            Satisfaction score (0-100) or None if insufficient data
        """
        # Collect all feedback for this agent
        agent_feedback = [fb for fb in self._feedback if fb.agent_variant_id == agent_variant_id]
        
        if len(agent_feedback) < 5:
            return None
        
        scores = []
        
        # Process ratings
        for fb in agent_feedback:
            if fb.feedback_type == FeedbackType.RATING and fb.rating is not None:
                # Convert 1-5 rating to 0-100
                scores.append((fb.rating / 5.0) * 100)
            elif fb.feedback_type == FeedbackType.THUMBS and fb.thumbs is not None:
                # Thumbs up = 100, thumbs down = 0
                scores.append(100 if fb.thumbs else 0)
        
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def get_top_issues(self, limit: int = 5) -> List[FeedbackInsight]:
        """Get top issues by severity and frequency"""
        # Analyze if not done
        if not self._insights:
            self.analyze_feedback()
        
        # Sort by severity (critical > high > medium > low) and supporting feedback count
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        sorted_insights = sorted(
            self._insights,
            key=lambda x: (severity_order.get(x.severity, 0), len(x.supporting_feedback)),
            reverse=True
        )
        
        return sorted_insights[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        total = len(self._feedback)
        
        if total == 0:
            return {
                "total_feedback": 0,
                "feedback_by_type": {},
                "avg_rating": None,
                "insights_count": 0
            }
        
        # Count by type
        type_counts = Counter(fb.feedback_type.value for fb in self._feedback)
        
        # Calculate average rating
        ratings = [fb.rating for fb in self._feedback if fb.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Thumbs ratio
        thumbs = [fb.thumbs for fb in self._feedback if fb.thumbs is not None]
        thumbs_up_ratio = sum(1 for t in thumbs if t) / len(thumbs) if thumbs else None
        
        return {
            "total_feedback": total,
            "feedback_by_type": dict(type_counts),
            "avg_rating": avg_rating,
            "thumbs_up_ratio": thumbs_up_ratio,
            "insights_count": len(self._insights),
            "feedback_by_agent": {
                variant: len([fb for fb in self._feedback if fb.agent_variant_id == variant])
                for variant in set(fb.agent_variant_id for fb in self._feedback)
            }
        }
