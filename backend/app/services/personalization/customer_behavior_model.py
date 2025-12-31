"""
Customer Behavior Modeling - Story 5.5.1

Predictive models of customer preferences, needs, and working patterns.
Enables agents to anticipate needs and customize outputs.

Epic 5.5: Hyper-Personalization & Adaptation (68 points)
Story Points: 21
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import statistics


# Try to import ML libraries, but allow graceful fallback
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TaskTiming(Enum):
    """When customer typically requests tasks"""
    MORNING = "morning"  # 6am-12pm
    AFTERNOON = "afternoon"  # 12pm-6pm
    EVENING = "evening"  # 6pm-12am
    NIGHT = "night"  # 12am-6am


class QualityPreference(Enum):
    """Customer's quality vs speed preferences"""
    DEPTH = "depth"  # Prefers thoroughness over speed
    SPEED = "speed"  # Prefers quick delivery over depth
    BALANCED = "balanced"  # Balanced approach
    CREATIVE = "creative"  # Prefers creative/novel approaches
    STRUCTURED = "structured"  # Prefers systematic/structured approaches


class LearningStyle(Enum):
    """Customer's learning and communication preferences"""
    VISUAL = "visual"  # Prefers charts, diagrams, visuals
    TEXTUAL = "textual"  # Prefers written explanations
    EXAMPLE_BASED = "example_based"  # Prefers concrete examples
    THEORY_BASED = "theory_based"  # Prefers theoretical explanations
    HANDS_ON = "hands_on"  # Prefers actionable steps


class CommunicationTone(Enum):
    """Preferred communication style"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SIMPLE = "simple"


@dataclass
class CustomerInteraction:
    """Record of a single customer interaction"""
    interaction_id: str
    customer_id: str
    agent_variant_id: str
    task_category: str
    task_description: str
    timestamp: datetime
    time_of_day: TaskTiming
    rating: Optional[float] = None  # 1.0 to 5.0
    completion_time_minutes: Optional[int] = None
    output_used: bool = False  # Did customer actually use the output?
    requested_changes: List[str] = field(default_factory=list)
    accepted_quickly: bool = False  # Accepted within 10 minutes
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskPattern:
    """Discovered pattern in customer's task behavior"""
    pattern_id: str
    customer_id: str
    pattern_type: str  # "frequent", "sequential", "temporal", "conditional"
    description: str
    task_categories: List[str]
    frequency: float  # How often this pattern occurs (0.0 to 1.0)
    confidence: float  # Confidence in pattern (0.0 to 1.0)
    last_occurrence: datetime
    occurrences: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "pattern_id": self.pattern_id,
            "customer_id": self.customer_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "task_categories": self.task_categories,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "last_occurrence": self.last_occurrence.isoformat(),
            "occurrences": self.occurrences,
            "metadata": self.metadata
        }


@dataclass
class CustomerProfile:
    """Comprehensive profile of customer preferences and behavior"""
    customer_id: str
    
    # Task patterns
    most_common_tasks: List[Tuple[str, float]] = field(default_factory=list)  # [(task, frequency)]
    typical_timing: TaskTiming = TaskTiming.AFTERNOON
    average_session_length: int = 30  # minutes
    task_frequency_per_week: float = 0.0
    
    # Quality preferences
    quality_preference: QualityPreference = QualityPreference.BALANCED
    prefers_explanations: bool = True
    detail_level_preference: float = 0.5  # 0.0 (minimal) to 1.0 (maximum)
    
    # Communication style
    communication_tone: CommunicationTone = CommunicationTone.FORMAL
    learning_style: LearningStyle = LearningStyle.TEXTUAL
    
    # Success indicators
    average_rating: float = 0.0
    task_acceptance_rate: float = 0.0  # % of tasks accepted without changes
    output_usage_rate: float = 0.0  # % of outputs actually used
    
    # Expertise level
    domain_expertise: Dict[str, str] = field(default_factory=dict)  # {task_category: level}
    
    # Metadata
    total_interactions: int = 0
    profile_confidence: float = 0.0  # How confident we are in this profile (0.0 to 1.0)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "customer_id": self.customer_id,
            "most_common_tasks": self.most_common_tasks,
            "typical_timing": self.typical_timing.value,
            "average_session_length": self.average_session_length,
            "task_frequency_per_week": self.task_frequency_per_week,
            "quality_preference": self.quality_preference.value,
            "prefers_explanations": self.prefers_explanations,
            "detail_level_preference": self.detail_level_preference,
            "communication_tone": self.communication_tone.value,
            "learning_style": self.learning_style.value,
            "average_rating": self.average_rating,
            "task_acceptance_rate": self.task_acceptance_rate,
            "output_usage_rate": self.output_usage_rate,
            "domain_expertise": self.domain_expertise,
            "total_interactions": self.total_interactions,
            "profile_confidence": self.profile_confidence,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class BehaviorPrediction:
    """Prediction about customer's next likely action or preference"""
    prediction_id: str
    customer_id: str
    prediction_type: str  # "next_task", "satisfaction", "style_preference"
    predicted_value: Any
    confidence: float  # 0.0 to 1.0
    reasoning: str
    features_used: Dict[str, Any]
    predicted_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CustomerBehaviorModel:
    """
    ML-powered customer behavior modeling.
    
    Builds predictive models of customer preferences, patterns, and needs.
    Enables agents to anticipate customer requirements and customize outputs.
    """
    
    def __init__(self):
        """Initialize customer behavior model"""
        self._interactions: Dict[str, List[CustomerInteraction]] = defaultdict(list)
        self._profiles: Dict[str, CustomerProfile] = {}
        self._patterns: Dict[str, List[TaskPattern]] = defaultdict(list)
        self._predictions: Dict[str, List[BehaviorPrediction]] = {}
        
        # ML models (only if sklearn available)
        self._task_predictor: Optional[Any] = None
        self._satisfaction_predictor: Optional[Any] = None
        self._is_trained: bool = False
        
        # Encoders for categorical features
        self._label_encoders: Dict[str, Any] = {}
        
        # Minimum data requirements
        self._min_interactions_for_profile: int = 10
        self._min_interactions_for_training: int = 50
        
        # Pattern detection thresholds
        self._pattern_frequency_threshold: float = 0.3  # Pattern must occur 30%+ of time
        self._pattern_confidence_threshold: float = 0.6  # 60% confidence minimum
    
    def record_interaction(self, interaction: CustomerInteraction) -> None:
        """
        Record a customer interaction.
        
        Args:
            interaction: Customer interaction to record
        """
        self._interactions[interaction.customer_id].append(interaction)
        
        # Update profile if enough data
        if len(self._interactions[interaction.customer_id]) >= self._min_interactions_for_profile:
            self._update_customer_profile(interaction.customer_id)
            self._detect_patterns(interaction.customer_id)
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """
        Get customer profile.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Customer profile or None if insufficient data
        """
        if customer_id not in self._profiles:
            # Try to build profile if we have enough data
            if len(self._interactions.get(customer_id, [])) >= self._min_interactions_for_profile:
                self._update_customer_profile(customer_id)
        
        return self._profiles.get(customer_id)
    
    def _update_customer_profile(self, customer_id: str) -> CustomerProfile:
        """
        Update customer profile based on interaction history.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Updated customer profile
        """
        interactions = self._interactions[customer_id]
        
        # Initialize or get existing profile
        profile = self._profiles.get(customer_id, CustomerProfile(customer_id=customer_id))
        
        # Update basic stats
        profile.total_interactions = len(interactions)
        
        # Most common tasks
        task_counts = Counter(i.task_category for i in interactions)
        total_tasks = len(interactions)
        profile.most_common_tasks = [
            (task, count / total_tasks)
            for task, count in task_counts.most_common(10)
        ]
        
        # Typical timing
        timing_counts = Counter(i.time_of_day for i in interactions)
        profile.typical_timing = timing_counts.most_common(1)[0][0]
        
        # Average session length (completion time)
        completion_times = [i.completion_time_minutes for i in interactions if i.completion_time_minutes]
        if completion_times:
            profile.average_session_length = int(statistics.mean(completion_times))
        
        # Task frequency per week
        if len(interactions) >= 2:
            date_range_days = (interactions[-1].timestamp - interactions[0].timestamp).days
            if date_range_days > 0:
                profile.task_frequency_per_week = (len(interactions) / date_range_days) * 7
        
        # Quality preferences (inferred from ratings and behavior)
        rated_interactions = [i for i in interactions if i.rating is not None]
        if rated_interactions:
            profile.average_rating = statistics.mean(i.rating for i in rated_interactions)
            
            # Infer quality preference from high-rated tasks
            high_rated = [i for i in rated_interactions if i.rating >= 4.0]
            if high_rated:
                avg_completion_time = statistics.mean(
                    i.completion_time_minutes for i in high_rated if i.completion_time_minutes
                ) if any(i.completion_time_minutes for i in high_rated) else 30
                
                # Longer completion times for high-rated tasks → prefers depth
                if avg_completion_time > 60:
                    profile.quality_preference = QualityPreference.DEPTH
                elif avg_completion_time < 20:
                    profile.quality_preference = QualityPreference.SPEED
                else:
                    profile.quality_preference = QualityPreference.BALANCED
        
        # Communication preferences
        # Infer from requested changes and acceptance patterns
        quick_accepts = sum(1 for i in interactions if i.accepted_quickly)
        profile.task_acceptance_rate = quick_accepts / len(interactions) if interactions else 0.0
        
        # Output usage rate
        used_outputs = sum(1 for i in interactions if i.output_used)
        profile.output_usage_rate = used_outputs / len(interactions) if interactions else 0.0
        
        # Detail level preference (infer from changes requested)
        changes_by_type = [
            change for i in interactions for change in i.requested_changes
        ]
        if changes_by_type:
            # If many "add more detail" requests → prefers high detail
            detail_requests = sum(1 for c in changes_by_type if "detail" in c.lower() or "more" in c.lower())
            brevity_requests = sum(1 for c in changes_by_type if "brief" in c.lower() or "shorter" in c.lower())
            
            if detail_requests > brevity_requests * 2:
                profile.detail_level_preference = 0.8
            elif brevity_requests > detail_requests * 2:
                profile.detail_level_preference = 0.3
            else:
                profile.detail_level_preference = 0.5
        
        # Explanation preference
        explanation_requests = sum(
            1 for i in interactions 
            for c in i.requested_changes 
            if "explain" in c.lower() or "why" in c.lower()
        )
        profile.prefers_explanations = explanation_requests > len(interactions) * 0.1
        
        # Profile confidence (based on data quantity and consistency)
        profile.profile_confidence = min(1.0, len(interactions) / 100.0)
        if profile.average_rating > 0:
            profile.profile_confidence = min(1.0, profile.profile_confidence + 0.2)
        
        profile.last_updated = datetime.now()
        
        # Store updated profile
        self._profiles[customer_id] = profile
        
        return profile
    
    def _detect_patterns(self, customer_id: str) -> List[TaskPattern]:
        """
        Detect patterns in customer's task behavior.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of detected patterns
        """
        interactions = self._interactions[customer_id]
        patterns = []
        
        # Pattern 1: Sequential tasks (X followed by Y)
        if len(interactions) >= 5:
            sequences = []
            for i in range(len(interactions) - 1):
                task_a = interactions[i].task_category
                task_b = interactions[i + 1].task_category
                # Only if within 24 hours
                time_diff = (interactions[i + 1].timestamp - interactions[i].timestamp).total_seconds() / 3600
                if time_diff <= 24:
                    sequences.append((task_a, task_b))
            
            if sequences:
                sequence_counts = Counter(sequences)
                for (task_a, task_b), count in sequence_counts.most_common(5):
                    frequency = count / (len(interactions) - 1)
                    if frequency >= self._pattern_frequency_threshold:
                        pattern = TaskPattern(
                            pattern_id=f"{customer_id}_seq_{len(patterns)}",
                            customer_id=customer_id,
                            pattern_type="sequential",
                            description=f"After {task_a}, customer typically requests {task_b}",
                            task_categories=[task_a, task_b],
                            frequency=frequency,
                            confidence=min(1.0, frequency + (count / 10)),
                            last_occurrence=interactions[-1].timestamp,
                            occurrences=count
                        )
                        patterns.append(pattern)
        
        # Pattern 2: Temporal patterns (tasks at specific times)
        timing_tasks = defaultdict(list)
        for interaction in interactions:
            timing_tasks[interaction.time_of_day].append(interaction.task_category)
        
        for timing, tasks in timing_tasks.items():
            task_counts = Counter(tasks)
            for task, count in task_counts.most_common(3):
                frequency = count / len(tasks)
                if frequency >= self._pattern_frequency_threshold:
                    pattern = TaskPattern(
                        pattern_id=f"{customer_id}_temp_{len(patterns)}",
                        customer_id=customer_id,
                        pattern_type="temporal",
                        description=f"Customer typically requests {task} during {timing.value}",
                        task_categories=[task],
                        frequency=frequency,
                        confidence=min(1.0, frequency + (count / 10)),
                        last_occurrence=interactions[-1].timestamp,
                        occurrences=count,
                        metadata={"timing": timing.value}
                    )
                    patterns.append(pattern)
        
        # Pattern 3: Frequent tasks (regardless of timing)
        task_counts = Counter(i.task_category for i in interactions)
        for task, count in task_counts.most_common(5):
            frequency = count / len(interactions)
            if frequency >= self._pattern_frequency_threshold:
                pattern = TaskPattern(
                    pattern_id=f"{customer_id}_freq_{len(patterns)}",
                    customer_id=customer_id,
                    pattern_type="frequent",
                    description=f"Customer frequently requests {task}",
                    task_categories=[task],
                    frequency=frequency,
                    confidence=min(1.0, frequency + (count / 20)),
                    last_occurrence=interactions[-1].timestamp,
                    occurrences=count
                )
                patterns.append(pattern)
        
        # Store patterns
        self._patterns[customer_id] = patterns
        
        return patterns
    
    def predict_next_task(
        self,
        customer_id: str,
        current_context: Optional[Dict[str, Any]] = None
    ) -> Optional[BehaviorPrediction]:
        """
        Predict customer's next likely task.
        
        Args:
            customer_id: Customer identifier
            current_context: Current context (e.g., last task, time of day)
            
        Returns:
            Prediction or None if insufficient data
        """
        profile = self.get_customer_profile(customer_id)
        if not profile or profile.total_interactions < 5:
            return None
        
        context = current_context or {}
        last_task = context.get("last_task")
        current_time_of_day = context.get("time_of_day", TaskTiming.AFTERNOON)
        
        # Check for sequential patterns first
        patterns = self._patterns.get(customer_id, [])
        sequential_patterns = [p for p in patterns if p.pattern_type == "sequential"]
        
        if last_task and sequential_patterns:
            # Find patterns that start with last_task
            matching_patterns = [
                p for p in sequential_patterns 
                if p.task_categories[0] == last_task
            ]
            if matching_patterns:
                # Use pattern with highest confidence
                best_pattern = max(matching_patterns, key=lambda p: p.confidence)
                predicted_task = best_pattern.task_categories[1]
                
                return BehaviorPrediction(
                    prediction_id=f"pred_{customer_id}_{datetime.now().timestamp()}",
                    customer_id=customer_id,
                    prediction_type="next_task",
                    predicted_value=predicted_task,
                    confidence=best_pattern.confidence,
                    reasoning=f"Pattern detected: {best_pattern.description} (occurred {best_pattern.occurrences} times)",
                    features_used={
                        "last_task": last_task,
                        "pattern_frequency": best_pattern.frequency,
                        "pattern_occurrences": best_pattern.occurrences
                    }
                )
        
        # Check for temporal patterns
        temporal_patterns = [
            p for p in patterns 
            if p.pattern_type == "temporal" and p.metadata.get("timing") == current_time_of_day.value
        ]
        if temporal_patterns:
            best_pattern = max(temporal_patterns, key=lambda p: p.confidence)
            predicted_task = best_pattern.task_categories[0]
            
            return BehaviorPrediction(
                prediction_id=f"pred_{customer_id}_{datetime.now().timestamp()}",
                customer_id=customer_id,
                prediction_type="next_task",
                predicted_value=predicted_task,
                confidence=best_pattern.confidence * 0.8,  # Slightly lower confidence for temporal
                reasoning=f"Time-based pattern: {best_pattern.description}",
                features_used={
                    "time_of_day": current_time_of_day.value,
                    "pattern_frequency": best_pattern.frequency
                }
            )
        
        # Fallback: Most common task
        if profile.most_common_tasks:
            most_common_task, frequency = profile.most_common_tasks[0]
            
            return BehaviorPrediction(
                prediction_id=f"pred_{customer_id}_{datetime.now().timestamp()}",
                customer_id=customer_id,
                prediction_type="next_task",
                predicted_value=most_common_task,
                confidence=frequency * 0.7,  # Lower confidence for frequency-based
                reasoning=f"Most common task ({frequency * 100:.0f}% of interactions)",
                features_used={
                    "task_frequency": frequency,
                    "total_interactions": profile.total_interactions
                }
            )
        
        return None
    
    def predict_satisfaction(
        self,
        customer_id: str,
        task_context: Dict[str, Any]
    ) -> Optional[BehaviorPrediction]:
        """
        Predict likely customer satisfaction for a task.
        
        Args:
            customer_id: Customer identifier
            task_context: Task context (category, complexity, etc.)
            
        Returns:
            Satisfaction prediction (1.0 to 5.0) or None
        """
        profile = self.get_customer_profile(customer_id)
        if not profile or profile.total_interactions < 5:
            return None
        
        task_category = task_context.get("task_category", "unknown")
        
        # Get historical satisfaction for this task type
        interactions = self._interactions[customer_id]
        similar_tasks = [
            i for i in interactions 
            if i.task_category == task_category and i.rating is not None
        ]
        
        if similar_tasks:
            avg_rating = statistics.mean(i.rating for i in similar_tasks)
            confidence = min(1.0, len(similar_tasks) / 10.0)
            
            return BehaviorPrediction(
                prediction_id=f"pred_{customer_id}_{datetime.now().timestamp()}",
                customer_id=customer_id,
                prediction_type="satisfaction",
                predicted_value=avg_rating,
                confidence=confidence,
                reasoning=f"Based on {len(similar_tasks)} similar tasks (avg rating: {avg_rating:.1f})",
                features_used={
                    "task_category": task_category,
                    "historical_rating": avg_rating,
                    "sample_size": len(similar_tasks)
                }
            )
        
        # Fallback: Overall average
        return BehaviorPrediction(
            prediction_id=f"pred_{customer_id}_{datetime.now().timestamp()}",
            customer_id=customer_id,
            prediction_type="satisfaction",
            predicted_value=profile.average_rating,
            confidence=0.5,  # Low confidence - using general average
            reasoning=f"Based on overall average rating: {profile.average_rating:.1f}",
            features_used={
                "overall_rating": profile.average_rating,
                "total_interactions": profile.total_interactions
            }
        )
    
    def get_style_preference(
        self,
        customer_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get customer's style preferences for current context.
        
        Args:
            customer_id: Customer identifier
            context: Optional context (task type, urgency, etc.)
            
        Returns:
            Dictionary of style preferences or None
        """
        profile = self.get_customer_profile(customer_id)
        if not profile:
            return None
        
        return {
            "communication_tone": profile.communication_tone.value,
            "detail_level": profile.detail_level_preference,
            "prefers_explanations": profile.prefers_explanations,
            "learning_style": profile.learning_style.value,
            "quality_preference": profile.quality_preference.value,
            "confidence": profile.profile_confidence
        }
    
    def get_patterns(self, customer_id: str) -> List[TaskPattern]:
        """
        Get detected patterns for customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of task patterns
        """
        return self._patterns.get(customer_id, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get model statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_customers = len(self._interactions)
        total_interactions = sum(len(interactions) for interactions in self._interactions.values())
        customers_with_profiles = len(self._profiles)
        total_patterns = sum(len(patterns) for patterns in self._patterns.values())
        
        return {
            "total_customers": total_customers,
            "total_interactions": total_interactions,
            "customers_with_profiles": customers_with_profiles,
            "average_interactions_per_customer": total_interactions / total_customers if total_customers > 0 else 0,
            "total_patterns_detected": total_patterns,
            "average_patterns_per_customer": total_patterns / total_customers if total_customers > 0 else 0,
            "is_trained": self._is_trained,
            "sklearn_available": SKLEARN_AVAILABLE
        }
