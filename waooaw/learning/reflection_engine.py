"""
Reflection Engine - Story 4.2

Self-assessment and learning from agent actions.
Part of Epic 4: Learning & Memory.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Outcome of an action."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class Action:
    """Record of an agent action."""
    action_id: str
    action_type: str  # pr_review, issue_creation, decision, etc.
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    outcome: OutcomeType
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """Reflection on an action."""
    action_id: str
    what_worked: List[str]
    what_failed: List[str]
    lessons_learned: List[str]
    improvement_suggestions: List[str]
    confidence_score: float  # 0-1
    timestamp: float = field(default_factory=time.time)


class ReflectionEngine:
    """
    Engine for agent self-reflection and learning.
    
    Features:
    - Analyze action outcomes
    - Extract patterns from success/failure
    - Generate improvement suggestions
    - Track learning progress
    - Build procedural knowledge
    """
    
    def __init__(self):
        """Initialize reflection engine."""
        self.actions_log: List[Action] = []
        self.reflections: Dict[str, Reflection] = {}
        
        # Pattern tracking
        self.success_patterns: Dict[str, int] = {}
        self.failure_patterns: Dict[str, int] = {}
        
        logger.info("ReflectionEngine initialized")
    
    def log_action(
        self,
        action_id: str,
        action_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        outcome: OutcomeType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Action:
        """
        Log an action for future reflection.
        
        Args:
            action_id: Unique action ID
            action_type: Type of action
            input_data: Input to action
            output_data: Output from action
            outcome: Success/failure/partial
            metadata: Additional context
            
        Returns:
            Action record
        """
        action = Action(
            action_id=action_id,
            action_type=action_type,
            input_data=input_data,
            output_data=output_data,
            outcome=outcome,
            metadata=metadata or {}
        )
        
        self.actions_log.append(action)
        
        logger.info(
            f"Action logged: {action_id} (type={action_type}, outcome={outcome.value})"
        )
        
        return action
    
    def reflect(self, action_id: str) -> Reflection:
        """
        Perform reflection on a specific action.
        
        Args:
            action_id: Action to reflect on
            
        Returns:
            Reflection with insights
        """
        # Find action
        action = self._find_action(action_id)
        if not action:
            raise ValueError(f"Action not found: {action_id}")
        
        # Analyze action
        what_worked = self._analyze_success(action)
        what_failed = self._analyze_failure(action)
        lessons = self._extract_lessons(action, what_worked, what_failed)
        suggestions = self._generate_suggestions(action, what_failed)
        confidence = self._calculate_confidence(action)
        
        # Create reflection
        reflection = Reflection(
            action_id=action_id,
            what_worked=what_worked,
            what_failed=what_failed,
            lessons_learned=lessons,
            improvement_suggestions=suggestions,
            confidence_score=confidence
        )
        
        self.reflections[action_id] = reflection
        
        # Update patterns
        self._update_patterns(action, what_worked, what_failed)
        
        logger.info(
            f"Reflection complete: {action_id} (lessons={len(lessons)}, confidence={confidence:.2f})"
        )
        
        return reflection
    
    def reflect_on_recent(self, count: int = 10) -> List[Reflection]:
        """
        Reflect on recent actions.
        
        Args:
            count: Number of recent actions to reflect on
            
        Returns:
            List of reflections
        """
        recent_actions = self.actions_log[-count:]
        reflections = []
        
        for action in recent_actions:
            if action.action_id not in self.reflections:
                reflection = self.reflect(action.action_id)
                reflections.append(reflection)
        
        return reflections
    
    def get_success_patterns(self, top_k: int = 5) -> List[tuple]:
        """
        Get most common success patterns.
        
        Args:
            top_k: Number of patterns to return
            
        Returns:
            List of (pattern, count) tuples
        """
        patterns = sorted(
            self.success_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return patterns[:top_k]
    
    def get_failure_patterns(self, top_k: int = 5) -> List[tuple]:
        """
        Get most common failure patterns.
        
        Args:
            top_k: Number of patterns to return
            
        Returns:
            List of (pattern, count) tuples
        """
        patterns = sorted(
            self.failure_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return patterns[:top_k]
    
    def get_lessons_by_type(self, action_type: str) -> List[str]:
        """
        Get all lessons learned for a specific action type.
        
        Args:
            action_type: Type of action (pr_review, decision, etc.)
            
        Returns:
            List of lessons
        """
        lessons = []
        
        for action in self.actions_log:
            if action.action_type == action_type:
                reflection = self.reflections.get(action.action_id)
                if reflection:
                    lessons.extend(reflection.lessons_learned)
        
        return list(set(lessons))  # Deduplicate
    
    def _find_action(self, action_id: str) -> Optional[Action]:
        """Find action by ID."""
        for action in self.actions_log:
            if action.action_id == action_id:
                return action
        return None
    
    def _analyze_success(self, action: Action) -> List[str]:
        """Analyze what worked in the action."""
        what_worked = []
        
        if action.outcome == OutcomeType.SUCCESS:
            # Check for positive indicators
            output = action.output_data
            
            if output.get("approved"):
                what_worked.append("Approval decision was correct")
            
            if output.get("violations_found", 0) > 0:
                what_worked.append("Successfully detected violations")
            
            if output.get("test_coverage", 0) >= 80:
                what_worked.append("Good test coverage check")
            
            # Check metadata for success factors
            if action.metadata.get("used_llm"):
                what_worked.append("LLM assistance was helpful")
            
            if action.metadata.get("used_deterministic_rules"):
                what_worked.append("Deterministic rules were effective")
        
        return what_worked
    
    def _analyze_failure(self, action: Action) -> List[str]:
        """Analyze what failed in the action."""
        what_failed = []
        
        if action.outcome in [OutcomeType.FAILURE, OutcomeType.PARTIAL]:
            # Check for failure indicators
            output = action.output_data
            
            if output.get("false_positive"):
                what_failed.append("False positive detection")
            
            if output.get("false_negative"):
                what_failed.append("Missed violations (false negative)")
            
            if output.get("timeout"):
                what_failed.append("Operation timed out")
            
            if action.metadata.get("error"):
                error = action.metadata["error"]
                what_failed.append(f"Error occurred: {error[:100]}")
        
        return what_failed
    
    def _extract_lessons(
        self,
        action: Action,
        what_worked: List[str],
        what_failed: List[str]
    ) -> List[str]:
        """Extract lessons from analysis."""
        lessons = []
        
        # Lessons from success
        if "deterministic rules were effective" in [w.lower() for w in what_worked]:
            lessons.append(f"For {action.action_type}: prioritize deterministic rules")
        
        if "llm assistance was helpful" in [w.lower() for w in what_worked]:
            lessons.append(f"For {action.action_type}: LLM improves decision quality")
        
        # Lessons from failure
        if any("false positive" in f.lower() for f in what_failed):
            lessons.append(f"For {action.action_type}: tighten violation detection criteria")
        
        if any("timeout" in f.lower() for f in what_failed):
            lessons.append(f"For {action.action_type}: implement timeout handling")
        
        return lessons
    
    def _generate_suggestions(
        self,
        action: Action,
        what_failed: List[str]
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if any("false positive" in f.lower() for f in what_failed):
            suggestions.append("Add more specific detection rules")
            suggestions.append("Increase confidence threshold")
        
        if any("false negative" in f.lower() for f in what_failed):
            suggestions.append("Broaden detection patterns")
            suggestions.append("Add more test cases")
        
        if any("timeout" in f.lower() for f in what_failed):
            suggestions.append("Optimize performance")
            suggestions.append("Implement caching")
        
        return suggestions
    
    def _calculate_confidence(self, action: Action) -> float:
        """Calculate confidence in analysis."""
        # Start with base confidence
        confidence = 0.5
        
        # Increase confidence if we have clear outcome
        if action.outcome == OutcomeType.SUCCESS:
            confidence += 0.3
        elif action.outcome == OutcomeType.FAILURE:
            confidence += 0.2
        
        # Increase if we have metadata
        if action.metadata:
            confidence += 0.1
        
        # Increase if similar actions exist
        similar_count = sum(
            1 for a in self.actions_log
            if a.action_type == action.action_type
        )
        if similar_count > 5:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _update_patterns(
        self,
        action: Action,
        what_worked: List[str],
        what_failed: List[str]
    ) -> None:
        """Update success/failure pattern tracking."""
        # Record success patterns
        if action.outcome == OutcomeType.SUCCESS:
            for pattern in what_worked:
                key = f"{action.action_type}:{pattern}"
                self.success_patterns[key] = self.success_patterns.get(key, 0) + 1
        
        # Record failure patterns
        if action.outcome in [OutcomeType.FAILURE, OutcomeType.PARTIAL]:
            for pattern in what_failed:
                key = f"{action.action_type}:{pattern}"
                self.failure_patterns[key] = self.failure_patterns.get(key, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        total_actions = len(self.actions_log)
        successes = sum(1 for a in self.actions_log if a.outcome == OutcomeType.SUCCESS)
        failures = sum(1 for a in self.actions_log if a.outcome == OutcomeType.FAILURE)
        
        return {
            "total_actions": total_actions,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / total_actions * 100) if total_actions > 0 else 0,
            "reflections_count": len(self.reflections),
            "success_patterns_count": len(self.success_patterns),
            "failure_patterns_count": len(self.failure_patterns)
        }
