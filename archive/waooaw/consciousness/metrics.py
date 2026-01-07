"""
Consciousness Metrics - Health Monitoring and Diagnostics

Story 4: Consciousness Metrics (Epic 2.4)
Points: 3

A conscious agent must be able to monitor its own health and diagnose
issues before they become critical. Like a human checking vital signs,
agents need to continuously assess their consciousness health.

This module provides:
1. Health Monitoring - Track identity, capability, awareness health
2. Diagnostic Checks - Identify potential issues
3. Health Scoring - Quantify overall consciousness health (0-100)
4. Alerting - Warn when health degrades
5. Recovery Recommendations - Suggest remediation actions
6. Historical Tracking - Monitor health trends over time

Health Dimensions:
- Identity Health: DID validity, credential freshness, attestation age
- Capability Health: Usage patterns, failure rates, rotation compliance
- Awareness Health: Environment monitoring, threat detection, resource status
- Reflection Health: Learning rate, insight generation, wisdom growth
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Overall health status levels"""

    CRITICAL = "critical"  # Immediate action required
    DEGRADED = "degraded"  # Performance impacted
    HEALTHY = "healthy"  # Operating normally
    OPTIMAL = "optimal"  # Peak performance


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConsciousnessMetrics:
    """
    Health monitoring and diagnostics for conscious agents.

    Tracks multiple dimensions of consciousness health and provides
    actionable diagnostics and recovery recommendations.

    Example:
        >>> metrics = ConsciousnessMetrics(agent_did="did:waooaw:agent:test")
        >>> 
        >>> # Update health data
        >>> metrics.update_identity_health(
        ...     credential_age_hours=12,
        ...     attestation_age_hours=2,
        ...     rotation_compliant=True
        ... )
        >>> 
        >>> # Get health report
        >>> report = metrics.get_health_report()
        >>> print(f"Health: {report['overall_status']}, Score: {report['health_score']}")
    """

    def __init__(
        self,
        agent_did: str,
        credential_max_age_hours: int = 168,  # 7 days
        attestation_max_age_hours: int = 24,  # 1 day
        capability_failure_threshold: float = 0.3,  # 30%
        min_reflection_interval_hours: int = 24,  # Daily reflection
    ):
        """
        Initialize consciousness metrics.

        Args:
            agent_did: DID of agent being monitored
            credential_max_age_hours: Max age for credentials
            attestation_max_age_hours: Max age for attestations
            capability_failure_threshold: Max acceptable failure rate
            min_reflection_interval_hours: Minimum reflection frequency
        """
        self.agent_did = agent_did

        # Thresholds
        self.credential_max_age_hours = credential_max_age_hours
        self.attestation_max_age_hours = attestation_max_age_hours
        self.capability_failure_threshold = capability_failure_threshold
        self.min_reflection_interval_hours = min_reflection_interval_hours

        # Health state
        self.identity_health: Dict[str, Any] = {}
        self.capability_health: Dict[str, Any] = {}
        self.awareness_health: Dict[str, Any] = {}
        self.reflection_health: Dict[str, Any] = {}

        # Alerts
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Historical tracking
        self.health_history: List[Dict[str, Any]] = []
        self.last_health_check: Optional[datetime] = None

        logger.info(f"Consciousness metrics initialized for {agent_did}")

    def update_identity_health(
        self,
        credential_age_hours: float,
        attestation_age_hours: float,
        rotation_compliant: bool,
        did_valid: bool = True,
    ) -> None:
        """
        Update identity health metrics.

        Args:
            credential_age_hours: Age of current credential
            attestation_age_hours: Age of current attestation
            rotation_compliant: Whether rotation schedule is followed
            did_valid: Whether DID is valid
        """
        self.identity_health = {
            "credential_age_hours": credential_age_hours,
            "attestation_age_hours": attestation_age_hours,
            "rotation_compliant": rotation_compliant,
            "did_valid": did_valid,
            "credential_expired": credential_age_hours > self.credential_max_age_hours,
            "attestation_stale": attestation_age_hours > self.attestation_max_age_hours,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check for alerts
        self._check_identity_alerts()

    def update_capability_health(
        self,
        total_invocations: int,
        failed_invocations: int,
        capabilities_count: int,
        rotation_overdue_count: int,
    ) -> None:
        """
        Update capability health metrics.

        Args:
            total_invocations: Total capability invocations
            failed_invocations: Number of failed invocations
            capabilities_count: Total capabilities loaded
            rotation_overdue_count: Capabilities overdue for rotation
        """
        failure_rate = (
            failed_invocations / total_invocations if total_invocations > 0 else 0.0
        )

        self.capability_health = {
            "total_invocations": total_invocations,
            "failed_invocations": failed_invocations,
            "failure_rate": failure_rate,
            "capabilities_count": capabilities_count,
            "rotation_overdue_count": rotation_overdue_count,
            "high_failure_rate": failure_rate > self.capability_failure_threshold,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check for alerts
        self._check_capability_alerts()

    def update_awareness_health(
        self,
        threat_level: str,
        resource_status: str,
        monitoring_active: bool,
        neighbors_count: int,
        last_assessment_age_minutes: Optional[float] = None,
    ) -> None:
        """
        Update awareness health metrics.

        Args:
            threat_level: Current threat level (none, low, medium, high, critical)
            resource_status: Resource status (abundant, healthy, constrained, critical)
            monitoring_active: Whether continuous monitoring is active
            neighbors_count: Number of discovered neighbors
            last_assessment_age_minutes: Time since last assessment
        """
        self.awareness_health = {
            "threat_level": threat_level,
            "resource_status": resource_status,
            "monitoring_active": monitoring_active,
            "neighbors_count": neighbors_count,
            "last_assessment_age_minutes": last_assessment_age_minutes,
            "high_threat": threat_level in ["high", "critical"],
            "critical_resources": resource_status == "critical",
            "monitoring_inactive": not monitoring_active,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check for alerts
        self._check_awareness_alerts()

    def update_reflection_health(
        self,
        total_reflections: int,
        total_insights: int,
        wisdom_score: float,
        last_reflection_age_hours: Optional[float] = None,
        action_count: int = 0,
    ) -> None:
        """
        Update reflection health metrics.

        Args:
            total_reflections: Total reflections performed
            total_insights: Total insights generated
            wisdom_score: Current wisdom score (0-100)
            last_reflection_age_hours: Hours since last reflection
            action_count: Total actions recorded
        """
        insights_per_reflection = (
            total_insights / total_reflections if total_reflections > 0 else 0.0
        )

        self.reflection_health = {
            "total_reflections": total_reflections,
            "total_insights": total_insights,
            "wisdom_score": wisdom_score,
            "last_reflection_age_hours": last_reflection_age_hours,
            "action_count": action_count,
            "insights_per_reflection": insights_per_reflection,
            "reflection_overdue": (
                last_reflection_age_hours is not None
                and last_reflection_age_hours > self.min_reflection_interval_hours
            ),
            "low_wisdom": wisdom_score < 30.0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check for alerts
        self._check_reflection_alerts()

    def _check_identity_alerts(self) -> None:
        """Check for identity health alerts"""
        if not self.identity_health:
            return

        # DID invalid
        if not self.identity_health.get("did_valid", True):
            self._add_alert(
                AlertLevel.CRITICAL,
                "Identity",
                "DID is invalid",
                "Verify DID registration and resolve any conflicts",
            )

        # Credential expired
        if self.identity_health.get("credential_expired"):
            self._add_alert(
                AlertLevel.ERROR,
                "Identity",
                f"Credential expired (age: {self.identity_health['credential_age_hours']:.1f}h)",
                "Rotate credential immediately to maintain security",
            )

        # Attestation stale
        if self.identity_health.get("attestation_stale"):
            self._add_alert(
                AlertLevel.WARNING,
                "Identity",
                f"Attestation is stale (age: {self.identity_health['attestation_age_hours']:.1f}h)",
                "Generate fresh attestation to prove current runtime state",
            )

        # Rotation non-compliant
        if not self.identity_health.get("rotation_compliant", True):
            self._add_alert(
                AlertLevel.WARNING,
                "Identity",
                "Not following rotation schedule",
                "Implement automated rotation to reduce security risk",
            )

    def _check_capability_alerts(self) -> None:
        """Check for capability health alerts"""
        if not self.capability_health:
            return

        # High failure rate
        if self.capability_health.get("high_failure_rate"):
            self._add_alert(
                AlertLevel.ERROR,
                "Capability",
                f"High failure rate ({self.capability_health['failure_rate']:.1%})",
                "Review capability implementations and error handling",
            )

        # Rotation overdue
        overdue = self.capability_health.get("rotation_overdue_count", 0)
        if overdue > 0:
            self._add_alert(
                AlertLevel.WARNING,
                "Capability",
                f"{overdue} capabilities overdue for rotation",
                "Rotate overdue capabilities to maintain security posture",
            )

        # No capabilities loaded
        if self.capability_health.get("capabilities_count", 0) == 0:
            self._add_alert(
                AlertLevel.INFO,
                "Capability",
                "No capabilities loaded",
                "Load capabilities to enable agent functionality",
            )

    def _check_awareness_alerts(self) -> None:
        """Check for awareness health alerts"""
        if not self.awareness_health:
            return

        # High threat
        if self.awareness_health.get("high_threat"):
            self._add_alert(
                AlertLevel.ERROR,
                "Awareness",
                f"High threat level: {self.awareness_health['threat_level']}",
                "Enable defensive mode and investigate threat source",
            )

        # Critical resources
        if self.awareness_health.get("critical_resources"):
            self._add_alert(
                AlertLevel.CRITICAL,
                "Awareness",
                "Critical resource status",
                "Reduce workload, pause non-essential tasks, scale resources",
            )

        # Monitoring inactive
        if self.awareness_health.get("monitoring_inactive"):
            self._add_alert(
                AlertLevel.WARNING,
                "Awareness",
                "Environment monitoring is not active",
                "Start continuous monitoring to maintain situational awareness",
            )

        # Assessment stale
        assessment_age = self.awareness_health.get("last_assessment_age_minutes")
        if assessment_age is not None and assessment_age > 10:  # 10 minutes
            self._add_alert(
                AlertLevel.INFO,
                "Awareness",
                f"Last assessment was {assessment_age:.1f} minutes ago",
                "Perform fresh assessment to update environmental state",
            )

    def _check_reflection_alerts(self) -> None:
        """Check for reflection health alerts"""
        if not self.reflection_health:
            return

        # Reflection overdue
        if self.reflection_health.get("reflection_overdue"):
            age = self.reflection_health.get("last_reflection_age_hours", 0)
            self._add_alert(
                AlertLevel.WARNING,
                "Reflection",
                f"Reflection overdue (last: {age:.1f}h ago)",
                "Perform reflection to learn from recent actions",
            )

        # Low wisdom
        if self.reflection_health.get("low_wisdom"):
            self._add_alert(
                AlertLevel.INFO,
                "Reflection",
                f"Low wisdom score ({self.reflection_health['wisdom_score']:.1f})",
                "Increase reflection frequency to accelerate learning",
            )

        # No reflections yet
        if self.reflection_health.get("total_reflections", 0) == 0:
            if self.reflection_health.get("action_count", 0) > 10:
                self._add_alert(
                    AlertLevel.INFO,
                    "Reflection",
                    "No reflections performed despite actions taken",
                    "Begin reflection cycle to enable learning from experience",
                )

    def _add_alert(
        self, level: AlertLevel, category: str, message: str, recommendation: str
    ) -> None:
        """Add a new alert"""
        alert = {
            "level": level.value,
            "category": category,
            "message": message,
            "recommendation": recommendation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Check if alert already exists (avoid duplicates)
        existing = [
            a
            for a in self.active_alerts
            if a["category"] == category and a["message"] == message
        ]

        if not existing:
            self.active_alerts.append(alert)
            self.alert_history.append(alert)

            # Log based on severity
            if level == AlertLevel.CRITICAL:
                logger.critical(f"🚨 {category}: {message}")
            elif level == AlertLevel.ERROR:
                logger.error(f"❌ {category}: {message}")
            elif level == AlertLevel.WARNING:
                logger.warning(f"⚠️  {category}: {message}")
            else:
                logger.info(f"ℹ️  {category}: {message}")

    def clear_alerts(self, category: Optional[str] = None) -> int:
        """
        Clear active alerts.

        Args:
            category: Optional category to clear (None = clear all)

        Returns:
            Number of alerts cleared
        """
        if category:
            cleared = [a for a in self.active_alerts if a["category"] == category]
            self.active_alerts = [
                a for a in self.active_alerts if a["category"] != category
            ]
        else:
            cleared = self.active_alerts
            self.active_alerts = []

        return len(cleared)

    def calculate_health_score(self) -> float:
        """
        Calculate overall health score (0-100).

        Based on:
        - Identity health (25%)
        - Capability health (25%)
        - Awareness health (25%)
        - Reflection health (25%)

        Returns:
            Health score from 0 (critical) to 100 (optimal)
        """
        identity_score = self._calculate_identity_score()
        capability_score = self._calculate_capability_score()
        awareness_score = self._calculate_awareness_score()
        reflection_score = self._calculate_reflection_score()

        # Weighted average (equal weights)
        total_score = (
            identity_score * 0.25
            + capability_score * 0.25
            + awareness_score * 0.25
            + reflection_score * 0.25
        )

        return round(total_score, 2)

    def _calculate_identity_score(self) -> float:
        """Calculate identity health score (0-100)"""
        if not self.identity_health:
            return 50.0  # Neutral score if no data

        score = 100.0

        # DID invalid: -100
        if not self.identity_health.get("did_valid", True):
            return 0.0

        # Credential expired: -50
        if self.identity_health.get("credential_expired"):
            score -= 50

        # Attestation stale: -20
        if self.identity_health.get("attestation_stale"):
            score -= 20

        # Not rotation compliant: -10
        if not self.identity_health.get("rotation_compliant", True):
            score -= 10

        # Credential age penalty (gradual)
        cred_age = self.identity_health.get("credential_age_hours", 0)
        if cred_age > 0:
            age_penalty = min((cred_age / self.credential_max_age_hours) * 20, 20)
            score -= age_penalty

        return max(score, 0.0)

    def _calculate_capability_score(self) -> float:
        """Calculate capability health score (0-100)"""
        if not self.capability_health:
            return 50.0  # Neutral score if no data

        score = 100.0

        # High failure rate: -50
        if self.capability_health.get("high_failure_rate"):
            score -= 50

        # Rotation overdue: -10 per capability (max -30)
        overdue = self.capability_health.get("rotation_overdue_count", 0)
        score -= min(overdue * 10, 30)

        # Failure rate penalty (gradual)
        failure_rate = self.capability_health.get("failure_rate", 0)
        if failure_rate > 0:
            failure_penalty = min(failure_rate * 100, 50)
            score -= failure_penalty

        # No capabilities: -20
        if self.capability_health.get("capabilities_count", 0) == 0:
            score -= 20

        return max(score, 0.0)

    def _calculate_awareness_score(self) -> float:
        """Calculate awareness health score (0-100)"""
        if not self.awareness_health:
            return 50.0  # Neutral score if no data

        score = 100.0

        # Critical resources: -70
        if self.awareness_health.get("critical_resources"):
            score -= 70

        # High threat: -40
        if self.awareness_health.get("high_threat"):
            score -= 40

        # Monitoring inactive: -30
        if self.awareness_health.get("monitoring_inactive"):
            score -= 30

        # Stale assessment: -10
        assessment_age = self.awareness_health.get("last_assessment_age_minutes")
        if assessment_age is not None and assessment_age > 10:
            score -= 10

        return max(score, 0.0)

    def _calculate_reflection_score(self) -> float:
        """Calculate reflection health score (0-100)"""
        if not self.reflection_health:
            return 50.0  # Neutral score if no data

        score = 100.0

        # Reflection overdue: -30
        if self.reflection_health.get("reflection_overdue"):
            score -= 30

        # Low wisdom: -20
        if self.reflection_health.get("low_wisdom"):
            score -= 20

        # No reflections but actions exist: -15
        if self.reflection_health.get("total_reflections", 0) == 0:
            if self.reflection_health.get("action_count", 0) > 10:
                score -= 15

        # Wisdom bonus (0-30 points)
        wisdom = self.reflection_health.get("wisdom_score", 0)
        if wisdom > 0:
            wisdom_bonus = min((wisdom / 100) * 30, 30)
            score += wisdom_bonus - 30  # Adjust from penalty-based calculation

        return max(score, 0.0)

    def determine_health_status(self, score: float) -> HealthStatus:
        """
        Determine health status from score.

        Args:
            score: Health score (0-100)

        Returns:
            Health status level
        """
        if score >= 90:
            return HealthStatus.OPTIMAL
        elif score >= 70:
            return HealthStatus.HEALTHY
        elif score >= 40:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.

        Returns:
            Health report with scores, status, alerts, and recommendations
        """
        # Calculate scores
        health_score = self.calculate_health_score()
        health_status = self.determine_health_status(health_score)

        # Component scores
        component_scores = {
            "identity": self._calculate_identity_score(),
            "capability": self._calculate_capability_score(),
            "awareness": self._calculate_awareness_score(),
            "reflection": self._calculate_reflection_score(),
        }

        # Build report
        report = {
            "agent_did": self.agent_did,
            "health_score": health_score,
            "overall_status": health_status.value,
            "component_scores": component_scores,
            "identity_health": self.identity_health.copy() if self.identity_health else {},
            "capability_health": self.capability_health.copy() if self.capability_health else {},
            "awareness_health": self.awareness_health.copy() if self.awareness_health else {},
            "reflection_health": self.reflection_health.copy() if self.reflection_health else {},
            "active_alerts": self.active_alerts.copy(),
            "alert_count_by_level": self._count_alerts_by_level(),
            "recommendations": self._generate_recommendations(health_score, health_status),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Record in history
        self.health_history.append(
            {
                "health_score": health_score,
                "status": health_status.value,
                "alert_count": len(self.active_alerts),
                "timestamp": report["timestamp"],
            }
        )

        self.last_health_check = datetime.now(timezone.utc)

        return report

    def _count_alerts_by_level(self) -> Dict[str, int]:
        """Count alerts by severity level"""
        counts = defaultdict(int)
        for alert in self.active_alerts:
            counts[alert["level"]] += 1
        return dict(counts)

    def _generate_recommendations(
        self, score: float, status: HealthStatus
    ) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []

        # Critical status
        if status == HealthStatus.CRITICAL:
            recommendations.append("URGENT: Consciousness health is critical - immediate action required")

        # Extract recommendations from active alerts (prioritize by level)
        alert_priority = {"critical": 4, "error": 3, "warning": 2, "info": 1}
        sorted_alerts = sorted(
            self.active_alerts,
            key=lambda a: alert_priority.get(a["level"], 0),
            reverse=True,
        )

        for alert in sorted_alerts[:5]:  # Top 5 alerts
            recommendations.append(f"[{alert['level'].upper()}] {alert['recommendation']}")

        # General recommendations based on score
        if score < 50:
            recommendations.append("Perform comprehensive health check and address all critical issues")
        elif score < 70:
            recommendations.append("Review and resolve active warnings to improve health")

        return recommendations

    def get_health_trend(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get health trend over time.

        Args:
            hours: Look-back period in hours

        Returns:
            Trend analysis with direction and change rate
        """
        if len(self.health_history) < 2:
            return {
                "trend": "insufficient_data",
                "data_points": len(self.health_history),
            }

        # Filter to time window
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_history = [
            h
            for h in self.health_history
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

        if len(recent_history) < 2:
            return {
                "trend": "insufficient_data",
                "data_points": len(recent_history),
            }

        # Calculate trend
        scores = [h["health_score"] for h in recent_history]
        first_score = scores[0]
        last_score = scores[-1]
        change = last_score - first_score

        # Determine trend direction
        if change > 5:
            trend = "improving"
        elif change < -5:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change": round(change, 2),
            "first_score": first_score,
            "last_score": last_score,
            "data_points": len(recent_history),
            "period_hours": hours,
        }
