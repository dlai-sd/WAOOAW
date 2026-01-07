"""
Tests for Self-Reflection Engine

Story 3: Self-Reflection (Epic 2.4)
Tests audit log analysis, pattern recognition, and learning from experience.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from waooaw.consciousness.reflection import (
    ReflectionEngine,
    ActionType,
    OutcomeType,
    InsightType,
)


class TestActionRecording:
    """Test action recording functionality"""

    @pytest.mark.asyncio
    async def test_record_action_success(self):
        """Test recording a successful action"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        action = await engine.record_action(
            action_type=ActionType.API_CALL,
            description="Fetch user data",
            outcome=OutcomeType.SUCCESS,
            duration_ms=150.5,
            context={"user_id": "123"},
        )

        assert action["agent_did"] == "did:waooaw:agent:test"
        assert action["action_type"] == "api_call"
        assert action["description"] == "Fetch user data"
        assert action["outcome"] == "success"
        assert action["duration_ms"] == 150.5
        assert action["context"]["user_id"] == "123"
        assert action["error"] is None
        assert "timestamp" in action
        assert "id" in action

    @pytest.mark.asyncio
    async def test_record_action_failure(self):
        """Test recording a failed action"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        action = await engine.record_action(
            action_type=ActionType.CAPABILITY_INVOCATION,
            description="Call external API",
            outcome=OutcomeType.ERROR,
            duration_ms=5000.0,
            error="Connection timeout",
        )

        assert action["outcome"] == "error"
        assert action["error"] == "Connection timeout"
        assert action["duration_ms"] == 5000.0

    @pytest.mark.asyncio
    async def test_action_history_storage(self):
        """Test that actions are stored in history"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record multiple actions
        await engine.record_action(
            ActionType.API_CALL, "Action 1", OutcomeType.SUCCESS, 100
        )
        await engine.record_action(
            ActionType.DECISION, "Action 2", OutcomeType.SUCCESS, 50
        )
        await engine.record_action(
            ActionType.TASK_EXECUTION, "Action 3", OutcomeType.FAILURE, 200
        )

        assert len(engine.action_history) == 3
        assert engine.action_history[0]["description"] == "Action 1"
        assert engine.action_history[1]["description"] == "Action 2"
        assert engine.action_history[2]["description"] == "Action 3"

    @pytest.mark.asyncio
    async def test_action_counters_updated(self):
        """Test that action and outcome counters are updated"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        await engine.record_action(
            ActionType.API_CALL, "Call 1", OutcomeType.SUCCESS, 100
        )
        await engine.record_action(
            ActionType.API_CALL, "Call 2", OutcomeType.SUCCESS, 120
        )
        await engine.record_action(
            ActionType.DECISION, "Decision 1", OutcomeType.FAILURE, 50
        )

        assert engine.action_count_by_type[ActionType.API_CALL] == 2
        assert engine.action_count_by_type[ActionType.DECISION] == 1
        assert engine.outcome_count_by_type[OutcomeType.SUCCESS] == 2
        assert engine.outcome_count_by_type[OutcomeType.FAILURE] == 1

    @pytest.mark.asyncio
    async def test_history_pruning(self):
        """Test that old history is pruned when max_history is exceeded"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test", max_history=5)

        # Record 7 actions (exceeds max of 5)
        for i in range(7):
            await engine.record_action(
                ActionType.API_CALL, f"Action {i}", OutcomeType.SUCCESS, 100
            )

        # Should only keep last 5
        assert len(engine.action_history) == 5
        assert engine.action_history[0]["description"] == "Action 2"
        assert engine.action_history[-1]["description"] == "Action 6"


class TestPatternAnalysis:
    """Test pattern recognition functionality"""

    @pytest.mark.asyncio
    async def test_detect_frequent_action_pattern(self):
        """Test detection of frequently repeated actions"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 5+ API calls (threshold for pattern detection)
        for i in range(6):
            await engine.record_action(
                ActionType.API_CALL, f"API call {i}", OutcomeType.SUCCESS, 100
            )

        insights = await engine.reflect()

        # Should detect pattern
        pattern_insights = [i for i in insights if i["type"] == "pattern"]
        assert len(pattern_insights) > 0

        pattern = pattern_insights[0]
        assert "api_call_frequency" in pattern["pattern_key"]
        assert pattern["frequency"] >= 5
        assert "success_rate" in pattern

    @pytest.mark.asyncio
    async def test_pattern_high_success_rate(self):
        """Test pattern detection with high success rate"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 5 successful API calls
        for i in range(5):
            await engine.record_action(
                ActionType.DATA_ACCESS, f"Data access {i}", OutcomeType.SUCCESS, 80
            )

        insights = await engine.reflect()

        pattern_insights = [i for i in insights if i["type"] == "pattern"]
        assert len(pattern_insights) > 0

        pattern = pattern_insights[0]
        assert pattern["success_rate"] >= 0.8
        assert "caching" in pattern["recommendation"].lower() or "batching" in pattern["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_pattern_low_success_rate(self):
        """Test pattern detection with low success rate"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 5 mostly failed actions
        for i in range(5):
            outcome = OutcomeType.FAILURE if i < 3 else OutcomeType.SUCCESS
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", outcome, 100
            )

        insights = await engine.reflect()

        pattern_insights = [i for i in insights if i["type"] == "pattern"]
        assert len(pattern_insights) > 0

        pattern = pattern_insights[0]
        assert pattern["success_rate"] < 0.8
        assert "failure" in pattern["recommendation"].lower()


class TestSuccessAnalysis:
    """Test analysis of successful actions"""

    @pytest.mark.asyncio
    async def test_identify_fast_successful_actions(self):
        """Test identification of fast successful operations"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 3+ fast successful API calls
        for i in range(4):
            await engine.record_action(
                ActionType.API_CALL, f"Fast call {i}", OutcomeType.SUCCESS, 50  # <100ms
            )

        insights = await engine.reflect()

        best_practice_insights = [i for i in insights if i["type"] == "best_practice"]
        assert len(best_practice_insights) > 0

        # Check for fast execution insight
        fast_insights = [
            i for i in best_practice_insights if "fast" in i["description"].lower()
        ]
        assert len(fast_insights) > 0
        assert fast_insights[0]["avg_duration_ms"] < 100

    @pytest.mark.asyncio
    async def test_identify_high_success_rate(self):
        """Test identification of high overall success rate"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record many successful actions (>90% success rate)
        for i in range(10):
            await engine.record_action(
                ActionType.TASK_EXECUTION, f"Task {i}", OutcomeType.SUCCESS, 200
            )

        insights = await engine.reflect()

        best_practice_insights = [i for i in insights if i["type"] == "best_practice"]
        
        # Should detect high success rate
        high_success = [
            i for i in best_practice_insights if "high" in i["description"].lower() and "success" in i["description"].lower()
        ]
        assert len(high_success) > 0
        assert high_success[0]["success_rate"] > 0.9

    @pytest.mark.asyncio
    async def test_success_strategies_stored(self):
        """Test that success strategies are stored"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record fast successful actions
        for i in range(4):
            await engine.record_action(
                ActionType.COMMUNICATION, f"Send message {i}", OutcomeType.SUCCESS, 30
            )

        await engine.reflect()

        assert len(engine.success_strategies) > 0


class TestFailureAnalysis:
    """Test analysis of failed actions"""

    @pytest.mark.asyncio
    async def test_identify_high_failure_rate(self):
        """Test identification of high failure rate for action type"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 10 API calls, 4 failures (40% failure rate)
        for i in range(10):
            outcome = OutcomeType.FAILURE if i < 4 else OutcomeType.SUCCESS
            await engine.record_action(
                ActionType.API_CALL, f"API call {i}", outcome, 100
            )

        insights = await engine.reflect()

        anti_pattern_insights = [i for i in insights if i["type"] == "anti_pattern"]
        assert len(anti_pattern_insights) > 0

        anti_pattern = anti_pattern_insights[0]
        assert anti_pattern["failure_rate"] > 0.3
        assert anti_pattern["action_type"] == "api_call"
        assert "review" in anti_pattern["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_identify_common_errors(self):
        """Test identification of common error patterns"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record multiple failures with same error
        for i in range(5):
            outcome = OutcomeType.ERROR if i < 3 else OutcomeType.SUCCESS
            error = "Database connection failed" if outcome == OutcomeType.ERROR else None
            await engine.record_action(
                ActionType.DATA_ACCESS, f"DB query {i}", outcome, 1000, error=error
            )

        insights = await engine.reflect()

        anti_pattern_insights = [i for i in insights if i["type"] == "anti_pattern"]
        assert len(anti_pattern_insights) > 0

        # Should identify common error
        insight = anti_pattern_insights[0]
        assert insight["common_error"] == "Database connection failed"

    @pytest.mark.asyncio
    async def test_identify_timeout_pattern(self):
        """Test identification of timeout patterns"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 2+ timeouts
        await engine.record_action(
            ActionType.API_CALL, "Slow call 1", OutcomeType.TIMEOUT, 5000
        )
        await engine.record_action(
            ActionType.API_CALL, "Slow call 2", OutcomeType.TIMEOUT, 5500
        )

        insights = await engine.reflect()

        risk_insights = [i for i in insights if i["type"] == "risk"]
        timeout_insights = [i for i in risk_insights if "timeout" in i["description"].lower()]
        
        assert len(timeout_insights) > 0
        assert timeout_insights[0]["timeout_count"] >= 2

    @pytest.mark.asyncio
    async def test_failure_patterns_stored(self):
        """Test that failure patterns are stored"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create failure pattern
        for i in range(5):
            outcome = OutcomeType.ERROR if i < 3 else OutcomeType.SUCCESS
            await engine.record_action(
                ActionType.TASK_EXECUTION, f"Task {i}", outcome, 100
            )

        await engine.reflect()

        assert len(engine.failure_patterns) > 0


class TestPerformanceAnalysis:
    """Test performance analysis functionality"""

    @pytest.mark.asyncio
    async def test_identify_slow_operations(self):
        """Test identification of slow operations"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record some slow actions (>1000ms)
        await engine.record_action(
            ActionType.DATA_ACCESS, "Slow query 1", OutcomeType.SUCCESS, 1500
        )
        await engine.record_action(
            ActionType.DATA_ACCESS, "Slow query 2", OutcomeType.SUCCESS, 2000
        )

        insights = await engine.reflect()

        optimization_insights = [i for i in insights if i["type"] == "optimization"]
        assert len(optimization_insights) > 0

        optimization = optimization_insights[0]
        assert optimization["avg_duration_ms"] > 1000
        assert "caching" in optimization["recommendation"].lower() or "async" in optimization["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_detect_performance_degradation(self):
        """Test detection of performance degradation over time"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 10 actions: first 5 fast, last 5 slow (degradation)
        for i in range(10):
            duration = 100 if i < 5 else 200  # 2x slower in second half
            await engine.record_action(
                ActionType.TASK_EXECUTION, f"Task {i}", OutcomeType.SUCCESS, duration
            )

        insights = await engine.reflect()

        risk_insights = [i for i in insights if i["type"] == "risk"]
        degradation_insights = [
            i for i in risk_insights if "degradation" in i["description"].lower()
        ]

        assert len(degradation_insights) > 0
        assert degradation_insights[0]["second_half_avg_ms"] > degradation_insights[0]["first_half_avg_ms"] * 1.5

    @pytest.mark.asyncio
    async def test_no_degradation_detected_for_stable_performance(self):
        """Test that no degradation is detected for stable performance"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record 10 actions with consistent performance
        for i in range(10):
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", OutcomeType.SUCCESS, 100
            )

        insights = await engine.reflect()

        risk_insights = [i for i in insights if i["type"] == "risk"]
        degradation_insights = [
            i for i in risk_insights if "degradation" in i["description"].lower()
        ]

        # Should not detect degradation
        assert len(degradation_insights) == 0


class TestReflectionProcess:
    """Test the reflection process itself"""

    @pytest.mark.asyncio
    async def test_reflection_with_no_actions(self):
        """Test reflection with no actions recorded"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        insights = await engine.reflect()

        assert insights == []
        assert engine.total_reflections == 1
        assert engine.last_reflection_time is not None

    @pytest.mark.asyncio
    async def test_reflection_window(self):
        """Test that only recent actions are analyzed"""
        engine = ReflectionEngine(
            agent_did="did:waooaw:agent:test", reflection_window_hours=1
        )

        # Record an action
        await engine.record_action(
            ActionType.API_CALL, "Recent", OutcomeType.SUCCESS, 100
        )

        # Manually add an old action
        old_action = {
            "id": "old-action",
            "agent_did": "did:waooaw:agent:test",
            "action_type": "api_call",
            "description": "Old action",
            "outcome": "success",
            "duration_ms": 100,
            "context": {},
            "error": None,
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        }
        engine.action_history.insert(0, old_action)

        # Reflect - should only see recent action
        insights = await engine.reflect()

        # The old action should be excluded from analysis
        # We can verify by checking that only 1 action was in the reflection window
        recent_actions = engine._get_recent_actions()
        assert len(recent_actions) == 1
        assert recent_actions[0]["description"] == "Recent"

    @pytest.mark.asyncio
    async def test_reflection_updates_metrics(self):
        """Test that reflection updates reflection metrics"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record actions
        for i in range(5):
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", OutcomeType.SUCCESS, 100
            )

        assert engine.total_reflections == 0
        assert engine.last_reflection_time is None

        await engine.reflect()

        assert engine.total_reflections == 1
        assert engine.last_reflection_time is not None

        await engine.reflect()

        assert engine.total_reflections == 2

    @pytest.mark.asyncio
    async def test_insights_stored(self):
        """Test that insights are stored"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create pattern
        for i in range(6):
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", OutcomeType.SUCCESS, 50
            )

        initial_insights = len(engine.insights)
        await engine.reflect()

        assert len(engine.insights) > initial_insights


class TestReflectionSummary:
    """Test summary generation"""

    def test_get_summary_with_no_actions(self):
        """Test summary with no actions"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        summary = engine.get_summary()

        assert summary["agent_did"] == "did:waooaw:agent:test"
        assert summary["total_actions"] == 0
        assert summary["action_breakdown"] == {}
        assert summary["outcome_breakdown"] == {}
        assert summary["total_insights"] == 0
        assert summary["total_reflections"] == 0
        assert summary["last_reflection"] is None
        assert summary["wisdom_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_summary_with_actions(self):
        """Test summary with recorded actions"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Record various actions
        await engine.record_action(
            ActionType.API_CALL, "Call 1", OutcomeType.SUCCESS, 100
        )
        await engine.record_action(
            ActionType.DECISION, "Decision 1", OutcomeType.SUCCESS, 50
        )
        await engine.record_action(
            ActionType.API_CALL, "Call 2", OutcomeType.FAILURE, 200
        )

        summary = engine.get_summary()

        assert summary["total_actions"] == 3
        assert summary["action_breakdown"]["api_call"] == 2
        assert summary["action_breakdown"]["decision"] == 1
        assert summary["outcome_breakdown"]["success"] == 2
        assert summary["outcome_breakdown"]["failure"] == 1

    @pytest.mark.asyncio
    async def test_wisdom_score_calculation(self):
        """Test wisdom score increases with learning"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        initial_wisdom = engine.get_summary()["wisdom_score"]

        # Record actions and reflect
        for i in range(6):
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", OutcomeType.SUCCESS, 50
            )

        await engine.reflect()

        final_wisdom = engine.get_summary()["wisdom_score"]

        # Wisdom should increase after reflection
        assert final_wisdom > initial_wisdom

    @pytest.mark.asyncio
    async def test_insight_breakdown_in_summary(self):
        """Test that summary includes insight type breakdown"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create patterns and successes
        for i in range(6):
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", OutcomeType.SUCCESS, 50
            )

        await engine.reflect()

        summary = engine.get_summary()

        assert "insight_breakdown" in summary
        assert isinstance(summary["insight_breakdown"], dict)


class TestRecommendations:
    """Test recommendation generation"""

    @pytest.mark.asyncio
    async def test_get_recommendations_with_no_insights(self):
        """Test recommendations with no insights"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        recommendations = await engine.get_recommendations()

        assert recommendations == []

    @pytest.mark.asyncio
    async def test_get_recommendations_from_insights(self):
        """Test that recommendations are extracted from insights"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create failure pattern
        for i in range(5):
            outcome = OutcomeType.ERROR if i < 3 else OutcomeType.SUCCESS
            await engine.record_action(
                ActionType.API_CALL, f"Call {i}", outcome, 100, error="Network error"
            )

        await engine.reflect()

        recommendations = await engine.get_recommendations()

        assert len(recommendations) > 0
        assert "recommendation" in recommendations[0]
        assert "priority" in recommendations[0]

    @pytest.mark.asyncio
    async def test_recommendations_sorted_by_priority(self):
        """Test that recommendations are sorted by priority"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create both high-priority (failures) and low-priority (patterns) insights
        # High priority: failures
        for i in range(5):
            outcome = OutcomeType.ERROR if i < 3 else OutcomeType.SUCCESS
            await engine.record_action(
                ActionType.API_CALL, f"Fail {i}", outcome, 100
            )

        # Lower priority: fast successes
        for i in range(4):
            await engine.record_action(
                ActionType.DECISION, f"Fast {i}", OutcomeType.SUCCESS, 30
            )

        await engine.reflect()

        recommendations = await engine.get_recommendations()

        # Recommendations should be sorted by priority (high to low)
        for i in range(len(recommendations) - 1):
            assert recommendations[i]["priority"] >= recommendations[i + 1]["priority"]

    @pytest.mark.asyncio
    async def test_high_priority_for_risks(self):
        """Test that risks get high priority"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        # Create timeout risk
        await engine.record_action(
            ActionType.API_CALL, "Timeout 1", OutcomeType.TIMEOUT, 5000
        )
        await engine.record_action(
            ActionType.API_CALL, "Timeout 2", OutcomeType.TIMEOUT, 5500
        )

        await engine.reflect()

        recommendations = await engine.get_recommendations()

        # Find risk recommendations
        risk_recs = [r for r in recommendations if r["insight_type"] == "risk"]
        assert len(risk_recs) > 0
        assert risk_recs[0]["priority"] >= 8  # Risks should be high priority


class TestReflectionEngineConfiguration:
    """Test engine configuration options"""

    def test_custom_max_history(self):
        """Test custom max history configuration"""
        engine = ReflectionEngine(
            agent_did="did:waooaw:agent:test", max_history=100
        )

        assert engine.max_history == 100

    def test_custom_reflection_window(self):
        """Test custom reflection window configuration"""
        engine = ReflectionEngine(
            agent_did="did:waooaw:agent:test", reflection_window_hours=48
        )

        assert engine.reflection_window_hours == 48

    def test_default_configuration(self):
        """Test default configuration values"""
        engine = ReflectionEngine(agent_did="did:waooaw:agent:test")

        assert engine.max_history == 1000
        assert engine.reflection_window_hours == 24
        assert engine.agent_did == "did:waooaw:agent:test"
        assert len(engine.action_history) == 0
        assert len(engine.insights) == 0
        assert engine.total_reflections == 0
