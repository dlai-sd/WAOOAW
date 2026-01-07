"""
Tests for Consciousness Metrics

Story 4: Consciousness Metrics (Epic 2.4)
Tests health monitoring, diagnostics, and alerting.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from waooaw.consciousness.metrics import (
    ConsciousnessMetrics,
    HealthStatus,
    AlertLevel,
)


class TestMetricsInitialization:
    """Test metrics initialization"""

    def test_initialize_with_defaults(self):
        """Test initialization with default settings"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        assert metrics.agent_did == "did:waooaw:agent:test"
        assert metrics.credential_max_age_hours == 168
        assert metrics.attestation_max_age_hours == 24
        assert metrics.capability_failure_threshold == 0.3
        assert metrics.min_reflection_interval_hours == 24
        assert len(metrics.active_alerts) == 0
        assert len(metrics.health_history) == 0

    def test_initialize_with_custom_thresholds(self):
        """Test initialization with custom thresholds"""
        metrics = ConsciousnessMetrics(
            agent_did="did:waooaw:agent:test",
            credential_max_age_hours=72,
            attestation_max_age_hours=12,
            capability_failure_threshold=0.2,
            min_reflection_interval_hours=12,
        )

        assert metrics.credential_max_age_hours == 72
        assert metrics.attestation_max_age_hours == 12
        assert metrics.capability_failure_threshold == 0.2
        assert metrics.min_reflection_interval_hours == 12


class TestIdentityHealth:
    """Test identity health tracking"""

    def test_update_identity_health_healthy(self):
        """Test updating identity health with healthy values"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_identity_health(
            credential_age_hours=24,
            attestation_age_hours=2,
            rotation_compliant=True,
            did_valid=True,
        )

        assert metrics.identity_health["credential_age_hours"] == 24
        assert metrics.identity_health["attestation_age_hours"] == 2
        assert metrics.identity_health["rotation_compliant"] is True
        assert metrics.identity_health["did_valid"] is True
        assert metrics.identity_health["credential_expired"] is False
        assert metrics.identity_health["attestation_stale"] is False

    def test_update_identity_health_expired_credential(self):
        """Test identity health with expired credential"""
        metrics = ConsciousnessMetrics(
            agent_did="did:waooaw:agent:test", credential_max_age_hours=168
        )

        metrics.update_identity_health(
            credential_age_hours=200,  # Expired
            attestation_age_hours=2,
            rotation_compliant=True,
        )

        assert metrics.identity_health["credential_expired"] is True
        
        # Should generate error alert
        error_alerts = [a for a in metrics.active_alerts if a["level"] == "error"]
        assert len(error_alerts) > 0
        assert "expired" in error_alerts[0]["message"].lower()

    def test_update_identity_health_stale_attestation(self):
        """Test identity health with stale attestation"""
        metrics = ConsciousnessMetrics(
            agent_did="did:waooaw:agent:test", attestation_max_age_hours=24
        )

        metrics.update_identity_health(
            credential_age_hours=12,
            attestation_age_hours=30,  # Stale
            rotation_compliant=True,
        )

        assert metrics.identity_health["attestation_stale"] is True

        # Should generate warning alert
        warning_alerts = [a for a in metrics.active_alerts if a["level"] == "warning"]
        assert len(warning_alerts) > 0
        assert "stale" in warning_alerts[0]["message"].lower()

    def test_update_identity_health_invalid_did(self):
        """Test identity health with invalid DID"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_identity_health(
            credential_age_hours=12,
            attestation_age_hours=2,
            rotation_compliant=True,
            did_valid=False,
        )

        assert metrics.identity_health["did_valid"] is False

        # Should generate critical alert
        critical_alerts = [
            a for a in metrics.active_alerts if a["level"] == "critical"
        ]
        assert len(critical_alerts) > 0
        assert "invalid" in critical_alerts[0]["message"].lower()


class TestCapabilityHealth:
    """Test capability health tracking"""

    def test_update_capability_health_healthy(self):
        """Test updating capability health with healthy values"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=5,
            capabilities_count=10,
            rotation_overdue_count=0,
        )

        assert metrics.capability_health["total_invocations"] == 100
        assert metrics.capability_health["failed_invocations"] == 5
        assert metrics.capability_health["failure_rate"] == 0.05
        assert metrics.capability_health["high_failure_rate"] is False

    def test_update_capability_health_high_failure_rate(self):
        """Test capability health with high failure rate"""
        metrics = ConsciousnessMetrics(
            agent_did="did:waooaw:agent:test", capability_failure_threshold=0.3
        )

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=40,  # 40% failure rate
            capabilities_count=10,
            rotation_overdue_count=0,
        )

        assert metrics.capability_health["failure_rate"] == 0.4
        assert metrics.capability_health["high_failure_rate"] is True

        # Should generate error alert
        error_alerts = [a for a in metrics.active_alerts if a["level"] == "error"]
        assert len(error_alerts) > 0
        assert "failure rate" in error_alerts[0]["message"].lower()

    def test_update_capability_health_rotation_overdue(self):
        """Test capability health with overdue rotations"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=5,
            capabilities_count=10,
            rotation_overdue_count=3,
        )

        assert metrics.capability_health["rotation_overdue_count"] == 3

        # Should generate warning alert
        warning_alerts = [a for a in metrics.active_alerts if a["level"] == "warning"]
        assert len(warning_alerts) > 0
        assert "overdue" in warning_alerts[0]["message"].lower()

    def test_update_capability_health_no_capabilities(self):
        """Test capability health with no capabilities loaded"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_capability_health(
            total_invocations=0,
            failed_invocations=0,
            capabilities_count=0,
            rotation_overdue_count=0,
        )

        assert metrics.capability_health["capabilities_count"] == 0

        # Should generate info alert
        info_alerts = [a for a in metrics.active_alerts if a["level"] == "info"]
        assert len(info_alerts) > 0


class TestAwarenessHealth:
    """Test awareness health tracking"""

    def test_update_awareness_health_healthy(self):
        """Test updating awareness health with healthy values"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="none",
            resource_status="healthy",
            monitoring_active=True,
            neighbors_count=3,
            last_assessment_age_minutes=2.0,
        )

        assert metrics.awareness_health["threat_level"] == "none"
        assert metrics.awareness_health["resource_status"] == "healthy"
        assert metrics.awareness_health["monitoring_active"] is True
        assert metrics.awareness_health["high_threat"] is False
        assert metrics.awareness_health["critical_resources"] is False

    def test_update_awareness_health_high_threat(self):
        """Test awareness health with high threat"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="critical",
            resource_status="healthy",
            monitoring_active=True,
            neighbors_count=3,
        )

        assert metrics.awareness_health["high_threat"] is True

        # Should generate error alert
        error_alerts = [a for a in metrics.active_alerts if a["level"] == "error"]
        assert len(error_alerts) > 0
        assert "threat" in error_alerts[0]["message"].lower()

    def test_update_awareness_health_critical_resources(self):
        """Test awareness health with critical resources"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="none",
            resource_status="critical",
            monitoring_active=True,
            neighbors_count=3,
        )

        assert metrics.awareness_health["critical_resources"] is True

        # Should generate critical alert
        critical_alerts = [
            a for a in metrics.active_alerts if a["level"] == "critical"
        ]
        assert len(critical_alerts) > 0
        assert "resource" in critical_alerts[0]["message"].lower()

    def test_update_awareness_health_monitoring_inactive(self):
        """Test awareness health with inactive monitoring"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="none",
            resource_status="healthy",
            monitoring_active=False,
            neighbors_count=3,
        )

        assert metrics.awareness_health["monitoring_inactive"] is True

        # Should generate warning alert
        warning_alerts = [a for a in metrics.active_alerts if a["level"] == "warning"]
        assert len(warning_alerts) > 0
        assert "monitoring" in warning_alerts[0]["message"].lower()


class TestReflectionHealth:
    """Test reflection health tracking"""

    def test_update_reflection_health_healthy(self):
        """Test updating reflection health with healthy values"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_reflection_health(
            total_reflections=10,
            total_insights=25,
            wisdom_score=65.0,
            last_reflection_age_hours=12.0,
            action_count=100,
        )

        assert metrics.reflection_health["total_reflections"] == 10
        assert metrics.reflection_health["total_insights"] == 25
        assert metrics.reflection_health["wisdom_score"] == 65.0
        assert metrics.reflection_health["insights_per_reflection"] == 2.5
        assert metrics.reflection_health["reflection_overdue"] is False
        assert metrics.reflection_health["low_wisdom"] is False

    def test_update_reflection_health_overdue(self):
        """Test reflection health with overdue reflection"""
        metrics = ConsciousnessMetrics(
            agent_did="did:waooaw:agent:test", min_reflection_interval_hours=24
        )

        metrics.update_reflection_health(
            total_reflections=5,
            total_insights=15,
            wisdom_score=50.0,
            last_reflection_age_hours=30.0,  # Overdue
            action_count=50,
        )

        assert metrics.reflection_health["reflection_overdue"] is True

        # Should generate warning alert
        warning_alerts = [a for a in metrics.active_alerts if a["level"] == "warning"]
        assert len(warning_alerts) > 0
        assert "overdue" in warning_alerts[0]["message"].lower()

    def test_update_reflection_health_low_wisdom(self):
        """Test reflection health with low wisdom"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_reflection_health(
            total_reflections=2,
            total_insights=3,
            wisdom_score=25.0,  # Low wisdom
            last_reflection_age_hours=10.0,
            action_count=20,
        )

        assert metrics.reflection_health["low_wisdom"] is True

        # Should generate info alert
        info_alerts = [a for a in metrics.active_alerts if a["level"] == "info"]
        assert len(info_alerts) > 0
        assert "wisdom" in info_alerts[0]["message"].lower()

    def test_update_reflection_health_no_reflections(self):
        """Test reflection health with no reflections but actions exist"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_reflection_health(
            total_reflections=0,
            total_insights=0,
            wisdom_score=0.0,
            last_reflection_age_hours=None,
            action_count=15,  # Actions exist but no reflections
        )

        # Should generate info alert
        info_alerts = [a for a in metrics.active_alerts if a["level"] == "info"]
        assert len(info_alerts) > 0


class TestHealthScoring:
    """Test health score calculations"""

    def test_calculate_identity_score_perfect(self):
        """Test identity score with perfect health"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_identity_health(
            credential_age_hours=12,
            attestation_age_hours=1,
            rotation_compliant=True,
            did_valid=True,
        )

        score = metrics._calculate_identity_score()
        assert score >= 90  # Should be near perfect

    def test_calculate_identity_score_invalid_did(self):
        """Test identity score with invalid DID"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_identity_health(
            credential_age_hours=12,
            attestation_age_hours=1,
            rotation_compliant=True,
            did_valid=False,
        )

        score = metrics._calculate_identity_score()
        assert score == 0.0  # Invalid DID = 0 score

    def test_calculate_capability_score_perfect(self):
        """Test capability score with perfect health"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=2,
            capabilities_count=10,
            rotation_overdue_count=0,
        )

        score = metrics._calculate_capability_score()
        assert score >= 90  # Should be near perfect

    def test_calculate_capability_score_high_failures(self):
        """Test capability score with high failure rate"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_capability_health(
            total_invocations=100,
            failed_invocations=50,  # 50% failure rate
            capabilities_count=10,
            rotation_overdue_count=0,
        )

        score = metrics._calculate_capability_score()
        assert score < 50  # Should be degraded

    def test_calculate_awareness_score_perfect(self):
        """Test awareness score with perfect health"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="none",
            resource_status="abundant",
            monitoring_active=True,
            neighbors_count=5,
            last_assessment_age_minutes=1.0,
        )

        score = metrics._calculate_awareness_score()
        assert score == 100.0  # Perfect score

    def test_calculate_awareness_score_critical(self):
        """Test awareness score with critical conditions"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_awareness_health(
            threat_level="critical",
            resource_status="critical",
            monitoring_active=False,
            neighbors_count=0,
        )

        score = metrics._calculate_awareness_score()
        assert score < 30  # Should be critical

    def test_calculate_reflection_score_perfect(self):
        """Test reflection score with excellent learning"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        metrics.update_reflection_health(
            total_reflections=20,
            total_insights=50,
            wisdom_score=95.0,
            last_reflection_age_hours=5.0,
            action_count=200,
        )

        score = metrics._calculate_reflection_score()
        assert score >= 90  # Should be excellent

    def test_calculate_overall_health_score(self):
        """Test overall health score calculation"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Set up healthy state
        metrics.update_identity_health(12, 1, True, True)
        metrics.update_capability_health(100, 5, 10, 0)
        metrics.update_awareness_health("none", "healthy", True, 3, 2.0)
        metrics.update_reflection_health(10, 25, 70.0, 12.0, 100)

        score = metrics.calculate_health_score()
        assert 0 <= score <= 100
        assert score >= 70  # Should be healthy overall


class TestHealthStatus:
    """Test health status determination"""

    def test_determine_status_optimal(self):
        """Test optimal status (>= 90)"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        status = metrics.determine_health_status(95.0)
        assert status == HealthStatus.OPTIMAL

    def test_determine_status_healthy(self):
        """Test healthy status (70-89)"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        status = metrics.determine_health_status(80.0)
        assert status == HealthStatus.HEALTHY

    def test_determine_status_degraded(self):
        """Test degraded status (40-69)"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        status = metrics.determine_health_status(55.0)
        assert status == HealthStatus.DEGRADED

    def test_determine_status_critical(self):
        """Test critical status (< 40)"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        status = metrics.determine_health_status(25.0)
        assert status == HealthStatus.CRITICAL


class TestAlertManagement:
    """Test alert management"""

    def test_clear_all_alerts(self):
        """Test clearing all alerts"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Generate some alerts
        metrics.update_identity_health(200, 30, False, True)
        
        initial_count = len(metrics.active_alerts)
        assert initial_count > 0

        cleared = metrics.clear_alerts()
        assert cleared == initial_count
        assert len(metrics.active_alerts) == 0

    def test_clear_category_alerts(self):
        """Test clearing alerts by category"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Generate identity and capability alerts
        metrics.update_identity_health(200, 30, False, True)
        metrics.update_capability_health(100, 40, 10, 2)

        identity_alerts = [
            a for a in metrics.active_alerts if a["category"] == "Identity"
        ]
        initial_identity_count = len(identity_alerts)

        cleared = metrics.clear_alerts(category="Identity")
        assert cleared == initial_identity_count

        # Identity alerts should be gone
        remaining_identity = [
            a for a in metrics.active_alerts if a["category"] == "Identity"
        ]
        assert len(remaining_identity) == 0

        # Other alerts should remain
        capability_alerts = [
            a for a in metrics.active_alerts if a["category"] == "Capability"
        ]
        assert len(capability_alerts) > 0

    def test_alerts_not_duplicated(self):
        """Test that duplicate alerts are not added"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Update same health condition twice
        metrics.update_identity_health(200, 2, True, True)
        initial_count = len(metrics.active_alerts)

        metrics.update_identity_health(200, 2, True, True)
        final_count = len(metrics.active_alerts)

        assert final_count == initial_count  # No duplicates added


class TestHealthReport:
    """Test health report generation"""

    def test_get_health_report_structure(self):
        """Test health report has correct structure"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Set up some health data
        metrics.update_identity_health(12, 1, True, True)
        metrics.update_capability_health(100, 5, 10, 0)

        report = metrics.get_health_report()

        # Check structure
        assert "agent_did" in report
        assert "health_score" in report
        assert "overall_status" in report
        assert "component_scores" in report
        assert "identity_health" in report
        assert "capability_health" in report
        assert "awareness_health" in report
        assert "reflection_health" in report
        assert "active_alerts" in report
        assert "alert_count_by_level" in report
        assert "recommendations" in report
        assert "timestamp" in report

    def test_get_health_report_updates_history(self):
        """Test that health report updates history"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        initial_history_len = len(metrics.health_history)

        metrics.update_identity_health(12, 1, True, True)
        report = metrics.get_health_report()

        assert len(metrics.health_history) == initial_history_len + 1
        assert metrics.last_health_check is not None

    def test_get_health_report_with_recommendations(self):
        """Test that critical health generates recommendations"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Create critical condition
        metrics.update_identity_health(12, 1, True, False)  # Invalid DID
        
        report = metrics.get_health_report()

        assert len(report["recommendations"]) > 0
        assert report["overall_status"] == "critical"


class TestHealthTrends:
    """Test health trend analysis"""

    def test_get_health_trend_insufficient_data(self):
        """Test trend with insufficient data"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        trend = metrics.get_health_trend()

        assert trend["trend"] == "insufficient_data"

    def test_get_health_trend_improving(self):
        """Test improving health trend"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Simulate improving health over time
        for i in range(5):
            metrics.update_identity_health(12 - i, 1, True, True)
            metrics.get_health_report()

        trend = metrics.get_health_trend()

        # With improving scores, trend should be positive
        assert trend["trend"] in ["improving", "stable"]
        assert "change" in trend

    def test_get_health_trend_degrading(self):
        """Test degrading health trend"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Simulate degrading health
        metrics.update_identity_health(12, 1, True, True)
        metrics.get_health_report()

        metrics.update_identity_health(200, 30, False, False)
        metrics.get_health_report()

        trend = metrics.get_health_trend()

        assert trend["trend"] == "degrading"
        assert trend["change"] < 0

    def test_get_health_trend_stable(self):
        """Test stable health trend"""
        metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")

        # Simulate stable health
        for _ in range(3):
            metrics.update_identity_health(12, 1, True, True)
            metrics.get_health_report()

        trend = metrics.get_health_trend()

        assert trend["trend"] == "stable"
        assert abs(trend["change"]) <= 5
