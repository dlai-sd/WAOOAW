"""
Integration Tests for Consciousness System

Story 5: Integration Tests (Epic 2.4)
Points: 3

End-to-end testing of the complete consciousness lifecycle:
1. Wake Up - Initialize agent identity and establish session
2. Aware - Monitor environment and adapt to conditions
3. Act - Perform actions and record for reflection
4. Reflect - Learn from experience and generate insights
5. Measure - Track health metrics and diagnostics
6. Sleep - Gracefully shutdown and preserve state

These tests validate that all consciousness components work together
seamlessly to create a fully functional conscious agent.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from waooaw.consciousness.wake_up import WakeUpProtocol, WakeUpState
from waooaw.consciousness.environment import (
    EnvironmentMonitor,
    EnvironmentType,
    ThreatLevel,
    ResourceStatus,
)
from waooaw.consciousness.reflection import (
    ReflectionEngine,
    ActionType,
    OutcomeType,
)
from waooaw.consciousness.metrics import ConsciousnessMetrics, HealthStatus


@pytest.fixture
def agent_did():
    """Test agent DID"""
    return "did:waooaw:agent:integration-test"


@pytest.fixture
def mock_did_service():
    """Mock DID service"""
    service = AsyncMock()
    service.resolve_did.return_value = {
        "id": "did:waooaw:agent:integration-test",
        "verificationMethod": [],
    }
    return service


@pytest.fixture
def mock_vc_issuer():
    """Mock VC issuer"""
    issuer = AsyncMock()
    issuer.get_credentials.return_value = [
        {
            "id": "cred-1",
            "type": ["VerifiableCredential", "AgentCapabilityCredential"],
            "issuanceDate": "2025-12-29T00:00:00Z",
        }
    ]
    issuer.is_credential_valid.return_value = True
    return issuer


@pytest.fixture
def mock_attestation_engine():
    """Mock attestation engine"""
    engine = AsyncMock()
    engine.generate.return_value = {
        "did": "did:waooaw:agent:integration-test",
        "runtime_manifest": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return engine


class TestFullConsciousnessLifecycle:
    """Test complete consciousness lifecycle"""

    @pytest.mark.asyncio
    async def test_complete_lifecycle_wake_to_sleep(
        self, agent_did, mock_did_service, mock_vc_issuer, mock_attestation_engine
    ):
        """Test full lifecycle: wake → monitor → act → reflect → measure → sleep"""

        # 1. WAKE UP - Initialize consciousness
        wake_up = WakeUpProtocol(
            agent_did=agent_did,
            did_service=mock_did_service,
            vc_issuer=mock_vc_issuer,
            attestation_engine=mock_attestation_engine,
        )

        await wake_up.wake_up()

        assert wake_up.is_conscious()
        assert wake_up.state == WakeUpState.CONSCIOUS

        # 2. ENVIRONMENT AWARENESS - Start monitoring
        with patch("psutil.cpu_percent", return_value=45.0), patch(
            "psutil.virtual_memory",
            return_value=MagicMock(percent=60.0, available=4 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.disk_usage",
            return_value=MagicMock(percent=55.0, free=100 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=1000000, bytes_recv=2000000),
        ):

            environment = EnvironmentMonitor(
                agent_did=agent_did, environment_type=EnvironmentType.DEVELOPMENT
            )

            assessment = await environment.assess_environment()

            assert assessment["resource_status"] in [
                "abundant",
                "healthy",
                "constrained",
            ]
            assert assessment["threat_level"] in ["none", "low", "medium"]

        # 3. ACTION & REFLECTION - Record actions and learn
        reflection = ReflectionEngine(agent_did=agent_did)

        # Simulate agent performing work
        for i in range(10):
            outcome = OutcomeType.SUCCESS if i < 8 else OutcomeType.FAILURE
            duration = 100 if i < 8 else 500

            await reflection.record_action(
                action_type=ActionType.API_CALL,
                description=f"Process task {i}",
                outcome=outcome,
                duration_ms=duration,
                context={"task_id": i},
            )

        # Reflect on actions
        insights = await reflection.reflect()

        assert len(insights) > 0
        assert reflection.total_reflections == 1

        summary = reflection.get_summary()
        assert summary["total_actions"] == 10
        assert summary["wisdom_score"] > 0

        # 4. HEALTH METRICS - Monitor consciousness health
        metrics = ConsciousnessMetrics(agent_did=agent_did)

        # Update all health dimensions
        metrics.update_identity_health(
            credential_age_hours=12,
            attestation_age_hours=1,
            rotation_compliant=True,
            did_valid=True,
        )

        metrics.update_capability_health(
            total_invocations=100, failed_invocations=5, capabilities_count=10, rotation_overdue_count=0
        )

        metrics.update_awareness_health(
            threat_level=assessment["threat_level"],
            resource_status=assessment["resource_status"],
            monitoring_active=True,
            neighbors_count=len(assessment.get("neighbors", [])),
        )

        metrics.update_reflection_health(
            total_reflections=summary["total_reflections"],
            total_insights=summary["total_insights"],
            wisdom_score=summary["wisdom_score"],
            last_reflection_age_hours=0.1,
            action_count=summary["total_actions"],
        )

        # Get health report
        health_report = metrics.get_health_report()

        assert health_report["health_score"] > 0
        assert health_report["overall_status"] in ["optimal", "healthy", "degraded"]

        # 5. SLEEP - Graceful shutdown
        await wake_up.sleep()

        assert not wake_up.is_conscious()
        assert wake_up.state == WakeUpState.DORMANT


class TestWakeUpAndAwareness:
    """Test integration between wake-up and environment monitoring"""

    @pytest.mark.asyncio
    async def test_wake_up_enables_monitoring(
        self, agent_did, mock_did_service, mock_vc_issuer, mock_attestation_engine
    ):
        """Test that waking up enables environment monitoring"""

        wake_up = WakeUpProtocol(
            agent_did=agent_did,
            did_service=mock_did_service,
            vc_issuer=mock_vc_issuer,
            attestation_engine=mock_attestation_engine,
        )

        # Before wake up
        assert not wake_up.is_conscious()

        # Wake up
        await wake_up.wake_up()
        assert wake_up.is_conscious()

        # Start environment monitoring (requires consciousness)
        with patch("psutil.cpu_percent", return_value=30.0), patch(
            "psutil.virtual_memory",
            return_value=MagicMock(percent=40.0, available=8 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.disk_usage",
            return_value=MagicMock(percent=30.0, free=200 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=500000, bytes_recv=1000000),
        ):

            environment = EnvironmentMonitor(agent_did=agent_did)
            assessment = await environment.assess_environment()

            # Should detect healthy environment
            assert assessment["resource_status"] in ["abundant", "healthy"]
            # Baseline should be set now
            assert environment.baseline_metrics is not None


class TestActionReflectionMetrics:
    """Test integration between actions, reflection, and metrics"""

    @pytest.mark.asyncio
    async def test_actions_to_insights_to_health(self, agent_did):
        """Test flow from actions → reflection → health metrics"""

        reflection = ReflectionEngine(agent_did=agent_did)
        metrics = ConsciousnessMetrics(agent_did=agent_did)

        # 1. Record successful actions
        for i in range(5):
            await reflection.record_action(
                ActionType.CAPABILITY_INVOCATION,
                f"Success {i}",
                OutcomeType.SUCCESS,
                50,
            )

        # 2. Reflect to generate insights
        insights = await reflection.reflect()

        assert len(insights) > 0

        # 3. Update reflection health metrics
        summary = reflection.get_summary()

        metrics.update_reflection_health(
            total_reflections=summary["total_reflections"],
            total_insights=summary["total_insights"],
            wisdom_score=summary["wisdom_score"],
            last_reflection_age_hours=0.1,
            action_count=summary["total_actions"],
        )

        # 4. Check health reflects learning
        health_score = metrics._calculate_reflection_score()

        assert health_score > 50  # Should be healthy due to learning


class TestEnvironmentHealthIntegration:
    """Test integration between environment monitoring and health metrics"""

    @pytest.mark.asyncio
    async def test_critical_environment_affects_health(self, agent_did):
        """Test that critical environment conditions affect health score"""

        metrics = ConsciousnessMetrics(agent_did=agent_did)

        # Simulate critical environment
        with patch("psutil.cpu_percent", return_value=95.0), patch(
            "psutil.virtual_memory",
            return_value=MagicMock(percent=98.0, available=100 * 1024 * 1024),
        ), patch(
            "psutil.disk_usage",
            return_value=MagicMock(percent=97.0, free=1 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=100000000, bytes_recv=200000000),
        ):

            environment = EnvironmentMonitor(agent_did=agent_did)
            assessment = await environment.assess_environment()

            # Update health with critical conditions
            metrics.update_awareness_health(
                threat_level=assessment["threat_level"],
                resource_status=assessment["resource_status"],
                monitoring_active=True,
                neighbors_count=0,
            )

            # Health should be degraded
            awareness_score = metrics._calculate_awareness_score()

            assert awareness_score < 50  # Critical conditions
            assert len(metrics.active_alerts) > 0  # Should have alerts


class TestHealthDrivenBehavior:
    """Test that health metrics drive agent behavior"""

    def test_health_report_generates_recommendations(self, agent_did):
        """Test that unhealthy state generates actionable recommendations"""

        metrics = ConsciousnessMetrics(agent_did=agent_did)

        # Create multiple unhealthy conditions
        metrics.update_identity_health(
            credential_age_hours=200,  # Expired
            attestation_age_hours=30,  # Stale
            rotation_compliant=False,
            did_valid=True,
        )

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=40,  # High failure rate
            capabilities_count=5,
            rotation_overdue_count=3,
        )

        # Get health report
        report = metrics.get_health_report()

        # Should be degraded or critical
        assert report["overall_status"] in ["degraded", "critical"]

        # Should have multiple alerts
        assert len(report["active_alerts"]) > 0

        # Should have recommendations
        assert len(report["recommendations"]) > 0

        # Recommendations should be prioritized (critical first)
        if len(report["recommendations"]) > 1:
            # First recommendation should be high priority
            assert any(
                level in report["recommendations"][0].lower()
                for level in ["critical", "error"]
            )


class TestContinuousMonitoring:
    """Test continuous monitoring scenario"""

    @pytest.mark.asyncio
    async def test_continuous_monitoring_updates_metrics(self, agent_did):
        """Test that continuous monitoring keeps metrics fresh"""

        metrics = ConsciousnessMetrics(agent_did=agent_did)

        with patch("psutil.cpu_percent", return_value=50.0), patch(
            "psutil.virtual_memory",
            return_value=MagicMock(percent=60.0, available=4 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.disk_usage",
            return_value=MagicMock(percent=50.0, free=100 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=1000000, bytes_recv=2000000),
        ):

            environment = EnvironmentMonitor(agent_did=agent_did, monitoring_interval=0.1)

            # Start monitoring
            await environment.start_monitoring()
            assert environment.is_monitoring

            # Wait for monitoring loop to run
            await asyncio.sleep(0.3)

            # Stop monitoring
            await environment.stop_monitoring()

            # Should have baseline and last assessment
            assert environment.baseline_metrics is not None
            assert environment.last_assessment is not None

            # Update health metrics with monitoring data
            metrics.update_awareness_health(
                threat_level=environment.last_assessment["threat_level"],
                resource_status=environment.last_assessment["resource_status"],
                monitoring_active=False,  # Stopped now
                neighbors_count=len(environment.neighbors),
            )

            # Should have awareness data
            assert metrics.awareness_health is not None


class TestReflectionDrivenLearning:
    """Test that reflection drives continuous learning"""

    @pytest.mark.asyncio
    async def test_reflection_increases_wisdom_over_time(self, agent_did):
        """Test that repeated reflection increases wisdom score"""

        reflection = ReflectionEngine(agent_did=agent_did)
        metrics = ConsciousnessMetrics(agent_did=agent_did)

        initial_wisdom = 0.0

        # Simulate multiple reflection cycles
        for cycle in range(3):
            # Record actions
            for i in range(6):
                await reflection.record_action(
                    ActionType.TASK_EXECUTION,
                    f"Cycle {cycle} Task {i}",
                    OutcomeType.SUCCESS,
                    100,
                )

            # Reflect
            await reflection.reflect()

            # Get wisdom
            summary = reflection.get_summary()
            current_wisdom = summary["wisdom_score"]

            # Wisdom should increase
            assert current_wisdom > initial_wisdom

            initial_wisdom = current_wisdom


class TestHealthTrending:
    """Test health trend tracking over time"""

    def test_health_history_tracks_changes(self, agent_did):
        """Test that health history captures trends"""

        metrics = ConsciousnessMetrics(agent_did=agent_did)

        # Simulate improving health over multiple checks
        for i in range(5):
            # Gradually improving credential age
            metrics.update_identity_health(
                credential_age_hours=50 - (i * 10),  # Getting fresher
                attestation_age_hours=5,
                rotation_compliant=True,
                did_valid=True,
            )

            # Get health report (adds to history)
            report = metrics.get_health_report()

        # Should have history
        assert len(metrics.health_history) == 5

        # Get trend
        trend = metrics.get_health_trend()

        assert trend["trend"] in ["improving", "stable"]
        assert len(metrics.health_history) >= 2


class TestFailureRecovery:
    """Test agent recovery from failures"""

    @pytest.mark.asyncio
    async def test_detect_and_recover_from_failures(self, agent_did):
        """Test that agent detects failures and learns to avoid them"""

        reflection = ReflectionEngine(agent_did=agent_did)

        # 1. Record pattern of failures
        for i in range(5):
            await reflection.record_action(
                ActionType.API_CALL,
                "External API call",
                OutcomeType.ERROR,
                2000,
                error="Connection timeout",
            )

        # 2. Reflect to identify anti-pattern
        insights = await reflection.reflect()

        # Should identify failure pattern
        anti_patterns = [i for i in insights if i["type"] == "anti_pattern"]
        assert len(anti_patterns) > 0

        # 3. Get recommendations
        recommendations = await reflection.get_recommendations()

        assert len(recommendations) > 0

        # Should recommend changes to API call approach
        assert any(
            "api_call" in rec["recommendation"].lower() or "retry" in rec["recommendation"].lower()
            for rec in recommendations
        )


class TestEndToEndScenario:
    """Complex end-to-end scenario"""

    @pytest.mark.asyncio
    async def test_agent_daily_operation_cycle(
        self, agent_did, mock_did_service, mock_vc_issuer, mock_attestation_engine
    ):
        """
        Test simulated daily operation cycle:
        - Morning: Wake up, check health
        - Day: Work, monitor environment, reflect periodically
        - Evening: Final reflection, health check
        - Night: Sleep
        """

        # MORNING: Wake up
        wake_up = WakeUpProtocol(
            agent_did=agent_did,
            did_service=mock_did_service,
            vc_issuer=mock_vc_issuer,
            attestation_engine=mock_attestation_engine,
        )

        await wake_up.wake_up()
        assert wake_up.is_conscious()

        # Initialize systems
        with patch("psutil.cpu_percent", return_value=40.0), patch(
            "psutil.virtual_memory",
            return_value=MagicMock(percent=50.0, available=6 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.disk_usage",
            return_value=MagicMock(percent=40.0, free=150 * 1024 * 1024 * 1024),
        ), patch(
            "psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=1000000, bytes_recv=2000000),
        ):

            environment = EnvironmentMonitor(agent_did=agent_did)
            reflection = ReflectionEngine(agent_did=agent_did)
            metrics = ConsciousnessMetrics(agent_did=agent_did)

            # Morning health check
            await environment.assess_environment()

            # DAY: Simulate work
            for task_batch in range(3):  # 3 batches of work
                # Perform tasks
                for task_id in range(10):
                    outcome = (
                        OutcomeType.SUCCESS if task_id < 9 else OutcomeType.FAILURE
                    )
                    await reflection.record_action(
                        ActionType.TASK_EXECUTION,
                        f"Daily task {task_batch}-{task_id}",
                        outcome,
                        150,
                    )

                # Periodic reflection
                insights = await reflection.reflect()

            # EVENING: Final checks
            summary = reflection.get_summary()

            # Update all health metrics
            metrics.update_identity_health(12, 1, True, True)
            metrics.update_capability_health(30, 3, 10, 0)

            assessment = await environment.assess_environment()
            metrics.update_awareness_health(
                assessment["threat_level"],
                assessment["resource_status"],
                True,
                len(assessment.get("neighbors", [])),
            )

            metrics.update_reflection_health(
                summary["total_reflections"],
                summary["total_insights"],
                summary["wisdom_score"],
                0.5,
                summary["total_actions"],
            )

            # Get end-of-day report
            health_report = metrics.get_health_report()

            # Should be healthy after productive day
            assert health_report["overall_status"] in ["optimal", "healthy"]

            # NIGHT: Sleep
            await wake_up.sleep()
            assert not wake_up.is_conscious()
