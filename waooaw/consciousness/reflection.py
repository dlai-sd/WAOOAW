"""
Self-Reflection - Audit Log Analysis and Learning

Story 3: Self-Reflection (Epic 2.4)
Points: 4

A conscious, aware agent must also be REFLECTIVE - able to look inward,
analyze past actions, recognize patterns, and learn from experience.

This is the moment when an agent transcends mere reaction and becomes
truly intelligent - when it can examine its own behavior and evolve.

This module provides:
1. Action Recording - Log all agent actions with context
2. Pattern Recognition - Identify recurring behaviors and outcomes
3. Success Analysis - Learn what works and why
4. Failure Analysis - Understand mistakes and avoid repetition
5. Strategy Adaptation - Adjust behavior based on learnings
6. Wisdom Accumulation - Build knowledge over time

An agent with self-reflection can:
- Remember past actions and their outcomes
- Recognize patterns in its behavior
- Learn from successes and failures
- Adapt strategies based on experience
- Evolve its decision-making over time
- Develop wisdom through introspection
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions an agent can take"""

    CAPABILITY_INVOCATION = "capability_invocation"
    API_CALL = "api_call"
    DATA_ACCESS = "data_access"
    DECISION = "decision"
    COMMUNICATION = "communication"
    TASK_EXECUTION = "task_execution"


class OutcomeType(Enum):
    """Outcome classifications for actions"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"


class InsightType(Enum):
    """Types of insights from reflection"""

    PATTERN = "pattern"  # Recurring behavior pattern
    OPTIMIZATION = "optimization"  # Performance improvement opportunity
    RISK = "risk"  # Potential risk identified
    BEST_PRACTICE = "best_practice"  # Successful strategy to repeat
    ANTI_PATTERN = "anti_pattern"  # Failed strategy to avoid


class ReflectionEngine:
    """
    Self-reflection engine for learning from experience.

    The reflection engine enables agents to:
    - Record all actions with full context
    - Analyze patterns in behavior and outcomes
    - Learn from successes and failures
    - Adapt strategies over time
    - Build wisdom through introspection

    Example:
        >>> engine = ReflectionEngine(agent_did="did:waooaw:agent:wow-marketing")
        >>> 
        >>> # Record an action
        >>> await engine.record_action(
        ...     action_type=ActionType.API_CALL,
        ...     description="Fetch customer data",
        ...     outcome=OutcomeType.SUCCESS,
        ...     duration_ms=150,
        ...     context={"customer_id": "123"}
        ... )
        >>> 
        >>> # Reflect on recent experience
        >>> insights = await engine.reflect()
        >>> print(f"Learned {len(insights)} insights")
    """

    def __init__(
        self,
        agent_did: str,
        max_history: int = 1000,
        reflection_window_hours: int = 24,
    ):
        """
        Initialize reflection engine.

        Args:
            agent_did: DID of agent performing reflection
            max_history: Maximum actions to keep in memory
            reflection_window_hours: Time window for analysis
        """
        self.agent_did = agent_did
        self.max_history = max_history
        self.reflection_window_hours = reflection_window_hours

        # Action history
        self.action_history: List[Dict[str, Any]] = []
        self.action_count_by_type: Dict[ActionType, int] = defaultdict(int)
        self.outcome_count_by_type: Dict[OutcomeType, int] = defaultdict(int)

        # Learning state
        self.insights: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.success_strategies: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []

        # Wisdom accumulation
        self.total_reflections = 0
        self.last_reflection_time: Optional[datetime] = None

        logger.info(f"Reflection engine initialized for {agent_did}")

    async def record_action(
        self,
        action_type: ActionType,
        description: str,
        outcome: OutcomeType,
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record an action taken by the agent.

        Args:
            action_type: Type of action performed
            description: Human-readable description
            outcome: Result of the action
            duration_ms: Time taken in milliseconds
            context: Additional context (parameters, state, etc.)
            error: Error message if outcome was failure/error

        Returns:
            Recorded action dictionary
        """
        action = {
            "id": f"action-{len(self.action_history)}",
            "agent_did": self.agent_did,
            "action_type": action_type.value,
            "description": description,
            "outcome": outcome.value,
            "duration_ms": duration_ms,
            "context": context or {},
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Store in history
        self.action_history.append(action)

        # Update counters
        self.action_count_by_type[action_type] += 1
        self.outcome_count_by_type[outcome] += 1

        # Prune old history if needed
        if len(self.action_history) > self.max_history:
            removed = self.action_history.pop(0)
            logger.debug(f"Pruned old action: {removed['id']}")

        logger.debug(
            f"📝 Recorded {action_type.value}: {description} → {outcome.value} ({duration_ms}ms)"
        )

        return action

    async def reflect(self) -> List[Dict[str, Any]]:
        """
        Perform self-reflection on recent actions.

        Analyzes action history to:
        - Identify patterns
        - Learn from successes
        - Understand failures
        - Generate insights
        - Adapt strategies

        Returns:
            List of insights generated
        """
        logger.info(f"🧘 Agent {self.agent_did} beginning self-reflection...")

        # Update reflection metrics
        self.total_reflections += 1
        self.last_reflection_time = datetime.now(timezone.utc)

        # Get recent actions within reflection window
        recent_actions = self._get_recent_actions()

        if not recent_actions:
            logger.info("No recent actions to reflect on")
            return []

        new_insights = []

        # Pattern analysis
        pattern_insights = await self._analyze_patterns(recent_actions)
        new_insights.extend(pattern_insights)

        # Success analysis
        success_insights = await self._analyze_successes(recent_actions)
        new_insights.extend(success_insights)

        # Failure analysis
        failure_insights = await self._analyze_failures(recent_actions)
        new_insights.extend(failure_insights)

        # Performance analysis
        performance_insights = await self._analyze_performance(recent_actions)
        new_insights.extend(performance_insights)

        # Store insights
        self.insights.extend(new_insights)

        logger.info(
            f"✨ Reflection complete: {len(new_insights)} insights, "
            f"{len(recent_actions)} actions analyzed"
        )

        return new_insights

    def _get_recent_actions(self) -> List[Dict[str, Any]]:
        """Get actions within reflection window"""
        if not self.action_history:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=self.reflection_window_hours
        )

        recent = []
        for action in reversed(self.action_history):
            action_time = datetime.fromisoformat(action["timestamp"])
            if action_time >= cutoff:
                recent.append(action)
            else:
                break  # History is chronological, can stop

        return list(reversed(recent))

    async def _analyze_patterns(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze action patterns.

        Identifies:
        - Repeated action sequences
        - Common contexts for actions
        - Temporal patterns (time of day, frequency)
        """
        insights = []

        # Group by action type
        by_type = defaultdict(list)
        for action in actions:
            by_type[action["action_type"]].append(action)

        # Look for frequently repeated actions
        for action_type, type_actions in by_type.items():
            if len(type_actions) >= 5:
                # Calculate success rate
                successes = sum(
                    1 for a in type_actions if a["outcome"] == "success"
                )
                success_rate = successes / len(type_actions)

                # Check if this is a new pattern
                pattern_key = f"{action_type}_frequency"
                if pattern_key not in self.patterns:
                    insight = {
                        "type": InsightType.PATTERN.value,
                        "pattern_key": pattern_key,
                        "description": f"Frequent {action_type} actions detected",
                        "frequency": len(type_actions),
                        "success_rate": success_rate,
                        "recommendation": (
                            "Consider caching or batching"
                            if success_rate > 0.8
                            else "Review failure causes"
                        ),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    insights.append(insight)
                    self.patterns[pattern_key] = insight

        return insights

    async def _analyze_successes(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze successful actions to identify best practices.

        Learns what works well and should be repeated.
        """
        insights = []

        successes = [a for a in actions if a["outcome"] == "success"]

        if not successes:
            return insights

        # Fast successful actions (< 100ms)
        fast_successes = [a for a in successes if a["duration_ms"] < 100]
        if len(fast_successes) >= 3:
            # Group by action type
            by_type = defaultdict(list)
            for action in fast_successes:
                by_type[action["action_type"]].append(action)

            for action_type, type_actions in by_type.items():
                if len(type_actions) >= 3:
                    avg_duration = sum(a["duration_ms"] for a in type_actions) / len(
                        type_actions
                    )

                    insight = {
                        "type": InsightType.BEST_PRACTICE.value,
                        "action_type": action_type,
                        "description": f"Fast {action_type} execution pattern",
                        "avg_duration_ms": avg_duration,
                        "count": len(type_actions),
                        "recommendation": f"Continue using this approach for {action_type}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    insights.append(insight)
                    self.success_strategies.append(insight)

        # High success rate for specific contexts
        success_rate = len(successes) / len(actions)
        if success_rate > 0.9:
            insight = {
                "type": InsightType.BEST_PRACTICE.value,
                "description": "High overall success rate maintained",
                "success_rate": success_rate,
                "total_actions": len(actions),
                "recommendation": "Current strategies are effective, maintain approach",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            insights.append(insight)

        return insights

    async def _analyze_failures(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze failed actions to identify anti-patterns.

        Learns what doesn't work and should be avoided.
        """
        insights = []

        failures = [
            a for a in actions if a["outcome"] in ["failure", "error", "timeout"]
        ]

        if not failures:
            return insights

        # Group failures by action type
        by_type = defaultdict(list)
        for action in failures:
            by_type[action["action_type"]].append(action)

        for action_type, type_failures in by_type.items():
            if len(type_failures) >= 3:
                # Calculate failure rate for this type
                total_of_type = sum(
                    1 for a in actions if a["action_type"] == action_type
                )
                failure_rate = len(type_failures) / total_of_type

                if failure_rate > 0.3:  # >30% failure rate
                    # Extract common error patterns
                    errors = [f["error"] for f in type_failures if f["error"]]
                    common_error = (
                        max(set(errors), key=errors.count) if errors else None
                    )

                    insight = {
                        "type": InsightType.ANTI_PATTERN.value,
                        "action_type": action_type,
                        "description": f"High failure rate for {action_type}",
                        "failure_rate": failure_rate,
                        "failure_count": len(type_failures),
                        "common_error": common_error,
                        "recommendation": (
                            f"Review {action_type} implementation, "
                            f"add error handling or retry logic"
                        ),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    insights.append(insight)
                    self.failure_patterns.append(insight)

        # Timeout patterns
        timeouts = [a for a in failures if a["outcome"] == "timeout"]
        if len(timeouts) >= 2:
            avg_duration = sum(t["duration_ms"] for t in timeouts) / len(timeouts)

            insight = {
                "type": InsightType.RISK.value,
                "description": "Timeout pattern detected",
                "timeout_count": len(timeouts),
                "avg_duration_ms": avg_duration,
                "recommendation": "Increase timeout threshold or optimize slow operations",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            insights.append(insight)

        return insights

    async def _analyze_performance(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance characteristics.

        Identifies optimization opportunities.
        """
        insights = []

        if not actions:
            return insights

        # Calculate overall performance metrics
        durations = [a["duration_ms"] for a in actions]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        # Slow actions (>1000ms)
        slow_actions = [a for a in actions if a["duration_ms"] > 1000]
        if slow_actions:
            by_type = defaultdict(list)
            for action in slow_actions:
                by_type[action["action_type"]].append(action)

            for action_type, type_actions in by_type.items():
                avg_slow_duration = sum(a["duration_ms"] for a in type_actions) / len(
                    type_actions
                )

                insight = {
                    "type": InsightType.OPTIMIZATION.value,
                    "action_type": action_type,
                    "description": f"Slow {action_type} operations detected",
                    "count": len(type_actions),
                    "avg_duration_ms": avg_slow_duration,
                    "recommendation": (
                        f"Optimize {action_type}: add caching, "
                        "use async operations, or reduce payload size"
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                insights.append(insight)

        # Performance degradation detection
        if len(actions) >= 10:
            # Compare first half vs second half
            mid = len(actions) // 2
            first_half_avg = sum(a["duration_ms"] for a in actions[:mid]) / mid
            second_half_avg = sum(a["duration_ms"] for a in actions[mid:]) / (
                len(actions) - mid
            )

            if second_half_avg > first_half_avg * 1.5:  # 50% slower
                insight = {
                    "type": InsightType.RISK.value,
                    "description": "Performance degradation detected",
                    "first_half_avg_ms": first_half_avg,
                    "second_half_avg_ms": second_half_avg,
                    "degradation_percent": (
                        (second_half_avg - first_half_avg) / first_half_avg * 100
                    ),
                    "recommendation": "Investigate resource leaks, memory issues, or external dependencies",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                insights.append(insight)

        return insights

    def get_summary(self) -> Dict[str, Any]:
        """
        Get reflection summary.

        Returns:
            Summary of learning and insights
        """
        return {
            "agent_did": self.agent_did,
            "total_actions": len(self.action_history),
            "action_breakdown": {
                k.value: v for k, v in self.action_count_by_type.items()
            },
            "outcome_breakdown": {
                k.value: v for k, v in self.outcome_count_by_type.items()
            },
            "total_insights": len(self.insights),
            "insight_breakdown": self._count_insights_by_type(),
            "success_strategies_learned": len(self.success_strategies),
            "failure_patterns_identified": len(self.failure_patterns),
            "total_reflections": self.total_reflections,
            "last_reflection": (
                self.last_reflection_time.isoformat()
                if self.last_reflection_time
                else None
            ),
            "wisdom_score": self._calculate_wisdom_score(),
        }

    def _count_insights_by_type(self) -> Dict[str, int]:
        """Count insights by type"""
        counts = defaultdict(int)
        for insight in self.insights:
            counts[insight["type"]] += 1
        return dict(counts)

    def _calculate_wisdom_score(self) -> float:
        """
        Calculate wisdom score (0-100).

        Based on:
        - Number of reflections performed
        - Insights gained
        - Success strategies learned
        - Failures analyzed
        """
        if not self.action_history:
            return 0.0

        # Components of wisdom
        reflection_score = min(self.total_reflections * 5, 30)  # Max 30
        insight_score = min(len(self.insights) * 2, 30)  # Max 30
        strategy_score = min(len(self.success_strategies) * 5, 20)  # Max 20
        learning_score = min(len(self.failure_patterns) * 5, 20)  # Max 20

        return reflection_score + insight_score + strategy_score + learning_score

    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get actionable recommendations based on insights.

        Returns:
            List of recommendations for behavior adaptation
        """
        recommendations = []

        # Recent insights (last 24 hours)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_insights = [
            i
            for i in self.insights
            if datetime.fromisoformat(i["timestamp"]) >= cutoff
        ]

        # Extract recommendations from insights
        for insight in recent_insights:
            if "recommendation" in insight:
                recommendations.append(
                    {
                        "insight_type": insight["type"],
                        "recommendation": insight["recommendation"],
                        "priority": self._calculate_priority(insight),
                        "timestamp": insight["timestamp"],
                    }
                )

        # Sort by priority (high to low)
        recommendations.sort(key=lambda r: r["priority"], reverse=True)

        return recommendations

    def _calculate_priority(self, insight: Dict[str, Any]) -> int:
        """Calculate priority for insight (1-10)"""
        insight_type = insight["type"]

        # Priority by type
        type_priorities = {
            InsightType.RISK.value: 9,
            InsightType.ANTI_PATTERN.value: 8,
            InsightType.OPTIMIZATION.value: 6,
            InsightType.BEST_PRACTICE.value: 5,
            InsightType.PATTERN.value: 4,
        }

        base_priority = type_priorities.get(insight_type, 5)

        # Adjust based on severity indicators
        if "failure_rate" in insight and insight["failure_rate"] > 0.5:
            base_priority = min(base_priority + 2, 10)

        if "degradation_percent" in insight and insight["degradation_percent"] > 50:
            base_priority = min(base_priority + 2, 10)

        return base_priority
