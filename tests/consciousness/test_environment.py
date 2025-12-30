"""
Tests for Environment Awareness

Story 2: Environment Awareness (Epic 2.4)
Coverage target: >90%

Tests verify:
1. Environment detection (kubernetes, serverless, edge, dev)
2. Resource assessment (CPU, memory, disk, network)
3. Threat detection (DoS, memory pressure, anomalies)
4. Neighbor discovery (agents, services, coordination)
5. Constraint identification (limits, quotas, policies)
6. Adaptive recommendations (behavior adjustments)
7. Safety checks (safe to operate determinations)
8. Continuous monitoring (start/stop/loop)
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from waooaw.consciousness.environment import (
    EnvironmentMonitor,
    EnvironmentType,
    ThreatLevel,
    ResourceStatus,
)


@pytest.fixture
def agent_did():
    """Test agent DID"""
    return "did:waooaw:agent:test-agent"


@pytest.fixture
def environment_monitor(agent_did):
    """Environment monitor instance"""
    return EnvironmentMonitor(agent_did=agent_did, monitoring_interval=0.1)


class TestEnvironmentDetection:
    """Tests for environment type detection"""

    @patch.dict("os.environ", {"KUBERNETES_SERVICE_HOST": "10.96.0.1"})
    def test_detect_kubernetes_environment(self, agent_did):
        """Test Kubernetes environment detection"""
        monitor = EnvironmentMonitor(agent_did=agent_did)
        assert monitor.environment_type == EnvironmentType.KUBERNETES

    @patch.dict("os.environ", {"AWS_LAMBDA_FUNCTION_NAME": "my-function"})
    def test_detect_serverless_environment(self, agent_did):
        """Test serverless environment detection"""
        monitor = EnvironmentMonitor(agent_did=agent_did)
        assert monitor.environment_type == EnvironmentType.SERVERLESS

    @patch.dict("os.environ", {"EDGE_RUNTIME": "cloudflare"})
    def test_detect_edge_environment(self, agent_did):
        """Test edge environment detection"""
        monitor = EnvironmentMonitor(agent_did=agent_did)
        assert monitor.environment_type == EnvironmentType.EDGE

    def test_detect_development_environment(self, agent_did):
        """Test development environment detection (default)"""
        monitor = EnvironmentMonitor(agent_did=agent_did)
        assert monitor.environment_type == EnvironmentType.DEVELOPMENT

    def test_explicit_environment_type(self, agent_did):
        """Test explicit environment type specification"""
        monitor = EnvironmentMonitor(
            agent_did=agent_did, environment_type=EnvironmentType.KUBERNETES
        )
        assert monitor.environment_type == EnvironmentType.KUBERNETES


class TestResourceAssessment:
    """Tests for resource monitoring"""

    @pytest.mark.asyncio
    async def test_assess_resources_success(self, environment_monitor):
        """Test successful resource assessment"""
        resources = await environment_monitor._assess_resources()

        assert "status" in resources
        assert isinstance(resources["status"], ResourceStatus)
        assert "metrics" in resources
        assert "cpu_percent" in resources["metrics"]
        assert "memory_percent" in resources["metrics"]
        assert "disk_percent" in resources["metrics"]
        assert "network_active" in resources["metrics"]

    @pytest.mark.asyncio
    async def test_resource_status_abundant(self, environment_monitor):
        """Test resource status classification - abundant"""
        with patch("psutil.cpu_percent", return_value=10.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk:
            mock_mem.return_value = Mock(percent=10.0, available=8 * 1024 * 1024 * 1024)
            mock_disk.return_value = Mock(
                percent=10.0, free=50 * 1024 * 1024 * 1024
            )

            resources = await environment_monitor._assess_resources()
            assert resources["status"] == ResourceStatus.ABUNDANT

    @pytest.mark.asyncio
    async def test_resource_status_healthy(self, environment_monitor):
        """Test resource status classification - healthy"""
        with patch("psutil.cpu_percent", return_value=40.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk:
            mock_mem.return_value = Mock(percent=40.0, available=4 * 1024 * 1024 * 1024)
            mock_disk.return_value = Mock(
                percent=40.0, free=20 * 1024 * 1024 * 1024
            )

            resources = await environment_monitor._assess_resources()
            assert resources["status"] == ResourceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_resource_status_constrained(self, environment_monitor):
        """Test resource status classification - constrained"""
        with patch("psutil.cpu_percent", return_value=70.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk:
            mock_mem.return_value = Mock(percent=70.0, available=2 * 1024 * 1024 * 1024)
            mock_disk.return_value = Mock(
                percent=70.0, free=5 * 1024 * 1024 * 1024
            )

            resources = await environment_monitor._assess_resources()
            assert resources["status"] == ResourceStatus.CONSTRAINED

    @pytest.mark.asyncio
    async def test_resource_status_critical(self, environment_monitor):
        """Test resource status classification - critical"""
        with patch("psutil.cpu_percent", return_value=95.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk:
            mock_mem.return_value = Mock(
                percent=95.0, available=0.5 * 1024 * 1024 * 1024
            )
            mock_disk.return_value = Mock(percent=95.0, free=1 * 1024 * 1024 * 1024)

            resources = await environment_monitor._assess_resources()
            assert resources["status"] == ResourceStatus.CRITICAL


class TestThreatDetection:
    """Tests for threat detection"""

    @pytest.mark.asyncio
    async def test_detect_threats_none(self, environment_monitor):
        """Test threat detection with no threats"""
        with patch("psutil.cpu_percent", return_value=30.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=40.0)
            mock_disk.return_value = Mock(percent=50.0)

            threats = await environment_monitor._detect_threats()
            assert threats["level"] == ThreatLevel.NONE
            assert len(threats["indicators"]) == 0

    @pytest.mark.asyncio
    async def test_detect_high_cpu_threat(self, environment_monitor):
        """Test detection of high CPU usage threat"""
        # Provide baseline assessment so CPU checks run
        environment_monitor.last_assessment = {
            "resource_metrics": {"cpu_percent": 50.0}
        }
        
        with patch("psutil.cpu_percent", return_value=95.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=40.0)
            mock_disk.return_value = Mock(percent=50.0)

            threats = await environment_monitor._detect_threats()
            assert threats["level"] == ThreatLevel.MEDIUM
            assert "high_cpu_usage" in threats["indicators"]

    @pytest.mark.asyncio
    async def test_detect_memory_exhaustion(self, environment_monitor):
        """Test detection of memory exhaustion"""
        with patch("psutil.cpu_percent", return_value=30.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=96.0)
            mock_disk.return_value = Mock(percent=50.0)

            threats = await environment_monitor._detect_threats()
            assert threats["level"] == ThreatLevel.HIGH
            assert "memory_exhaustion" in threats["indicators"]

    @pytest.mark.asyncio
    async def test_detect_memory_pressure(self, environment_monitor):
        """Test detection of memory pressure (not exhaustion)"""
        with patch("psutil.cpu_percent", return_value=30.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=88.0)
            mock_disk.return_value = Mock(percent=50.0)

            threats = await environment_monitor._detect_threats()
            assert threats["level"] == ThreatLevel.MEDIUM
            assert "memory_pressure" in threats["indicators"]

    @pytest.mark.asyncio
    async def test_detect_disk_full(self, environment_monitor):
        """Test detection of disk full"""
        with patch("psutil.cpu_percent", return_value=30.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=40.0)
            mock_disk.return_value = Mock(percent=96.0)

            threats = await environment_monitor._detect_threats()
            assert threats["level"] == ThreatLevel.HIGH
            assert "disk_full" in threats["indicators"]

    @pytest.mark.asyncio
    async def test_detect_cpu_spike(self, environment_monitor):
        """Test detection of CPU spike"""
        # Set baseline
        environment_monitor.last_assessment = {
            "resource_metrics": {"cpu_percent": 20.0}
        }

        with patch("psutil.cpu_percent", return_value=50.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=40.0)
            mock_disk.return_value = Mock(percent=50.0)

            threats = await environment_monitor._detect_threats()
            assert "cpu_spike" in threats["indicators"]

    @pytest.mark.asyncio
    async def test_threat_history_tracking(self, environment_monitor):
        """Test threat history is tracked"""
        environment_monitor.last_assessment = {
            "resource_metrics": {"cpu_percent": 50.0}
        }
        
        with patch("psutil.cpu_percent", return_value=95.0), patch(
            "psutil.virtual_memory"
        ) as mock_mem, patch("psutil.disk_usage") as mock_disk, patch("psutil.pids", return_value=list(range(100))):
            mock_mem.return_value = Mock(percent=40.0)
            mock_disk.return_value = Mock(percent=50.0)

            await environment_monitor._detect_threats()
            assert len(environment_monitor.threat_history) == 1
            assert environment_monitor.threat_history[0]["level"] == "medium"


class TestNeighborDiscovery:
    """Tests for neighbor discovery"""

    @pytest.mark.asyncio
    async def test_discover_neighbors_development(self, environment_monitor):
        """Test neighbor discovery in development environment"""
        with patch("psutil.process_iter", return_value=[]):
            neighbors = await environment_monitor._discover_neighbors()
            assert isinstance(neighbors, set)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"POD_NAMESPACE": "production"})
    async def test_discover_neighbors_kubernetes(self, agent_did):
        """Test neighbor discovery in Kubernetes"""
        monitor = EnvironmentMonitor(
            agent_did=agent_did, environment_type=EnvironmentType.KUBERNETES
        )

        with patch.dict(
            "os.environ",
            {"AGENT_NEIGHBORS": "did:waooaw:agent:agent1,did:waooaw:agent:agent2"},
        ):
            neighbors = await monitor._discover_neighbors()
            assert len(neighbors) == 2
            assert "did:waooaw:agent:agent1" in neighbors
            assert "did:waooaw:agent:agent2" in neighbors

    @pytest.mark.asyncio
    async def test_neighbor_state_tracking(self, agent_did):
        """Test neighbor state is tracked"""
        with patch.dict(
            "os.environ", {"AGENT_NEIGHBORS": "did:waooaw:agent:neighbor1"}
        ), patch("psutil.process_iter", return_value=[]):
            # Create monitor in Kubernetes mode so it checks AGENT_NEIGHBORS env var
            monitor = EnvironmentMonitor(agent_did=agent_did, environment_type=EnvironmentType.KUBERNETES)
            await monitor._discover_neighbors()
            assert len(monitor.neighbors) == 1


class TestConstraintIdentification:
    """Tests for constraint identification"""

    @pytest.mark.asyncio
    async def test_identify_constraints_development(self, environment_monitor):
        """Test constraint identification in development"""
        constraints = await environment_monitor._identify_constraints()

        assert "cpu_limit" in constraints
        assert "memory_limit_mb" in constraints
        assert "disk_quota_gb" in constraints

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "2048"})
    async def test_identify_constraints_serverless(self, agent_did):
        """Test constraint identification in serverless"""
        monitor = EnvironmentMonitor(
            agent_did=agent_did, environment_type=EnvironmentType.SERVERLESS
        )

        constraints = await monitor._identify_constraints()
        assert constraints["memory_limit_mb"] == 2048


class TestEnvironmentAssessment:
    """Tests for complete environment assessment"""

    @pytest.mark.asyncio
    async def test_assess_environment_complete(self, environment_monitor):
        """Test complete environment assessment"""
        assessment = await environment_monitor.assess_environment()

        # Verify all required fields
        assert "agent_did" in assessment
        assert "environment_type" in assessment
        assert "resource_status" in assessment
        assert "resource_metrics" in assessment
        assert "threat_level" in assessment
        assert "threat_indicators" in assessment
        assert "neighbors" in assessment
        assert "neighbor_count" in assessment
        assert "constraints" in assessment
        assert "timestamp" in assessment

    @pytest.mark.asyncio
    async def test_assessment_stores_last_assessment(self, environment_monitor):
        """Test assessment is stored"""
        assessment = await environment_monitor.assess_environment()
        assert environment_monitor.last_assessment == assessment

    @pytest.mark.asyncio
    async def test_assessment_sets_baseline(self, environment_monitor):
        """Test first assessment sets baseline metrics"""
        assert environment_monitor.baseline_metrics is None

        await environment_monitor.assess_environment()

        assert environment_monitor.baseline_metrics is not None
        assert "cpu_percent" in environment_monitor.baseline_metrics


class TestAdaptiveRecommendations:
    """Tests for adaptive behavior recommendations"""

    @pytest.mark.asyncio
    async def test_recommendations_critical_resources(self, environment_monitor):
        """Test recommendations for critical resources"""
        environment_monitor.last_assessment = {
            "resource_status": "critical",
            "threat_level": "none",
            "neighbor_count": 0,
        }

        recs = environment_monitor.get_adaptive_recommendations()
        assert "reduce_concurrency" in recs["recommendations"]
        assert "pause_non_essential_tasks" in recs["recommendations"]

    @pytest.mark.asyncio
    async def test_recommendations_abundant_resources(self, environment_monitor):
        """Test recommendations for abundant resources"""
        environment_monitor.last_assessment = {
            "resource_status": "abundant",
            "threat_level": "none",
            "neighbor_count": 0,
        }

        recs = environment_monitor.get_adaptive_recommendations()
        assert "increase_concurrency" in recs["recommendations"]
        assert "precompute_results" in recs["recommendations"]

    @pytest.mark.asyncio
    async def test_recommendations_high_threats(self, environment_monitor):
        """Test recommendations for high threat level"""
        environment_monitor.last_assessment = {
            "resource_status": "healthy",
            "threat_level": "critical",
            "neighbor_count": 0,
        }

        recs = environment_monitor.get_adaptive_recommendations()
        assert "enable_defense_mode" in recs["recommendations"]

    @pytest.mark.asyncio
    async def test_recommendations_many_neighbors(self, environment_monitor):
        """Test recommendations for many neighbors"""
        environment_monitor.last_assessment = {
            "resource_status": "healthy",
            "threat_level": "none",
            "neighbor_count": 15,
        }

        recs = environment_monitor.get_adaptive_recommendations()
        assert "enable_coordination" in recs["recommendations"]

    def test_recommendations_no_assessment(self, environment_monitor):
        """Test recommendations with no assessment"""
        recs = environment_monitor.get_adaptive_recommendations()
        assert "reason" in recs
        assert recs["reason"] == "No assessment available"


class TestSafetyChecks:
    """Tests for safety determination"""

    def test_is_safe_no_assessment(self, environment_monitor):
        """Test safety check with no assessment (assume safe)"""
        assert environment_monitor.is_safe_to_operate() is True

    def test_is_safe_critical_threat(self, environment_monitor):
        """Test safety check with critical threat"""
        environment_monitor.last_assessment = {
            "threat_level": "critical",
            "resource_status": "healthy",
        }
        assert environment_monitor.is_safe_to_operate() is False

    def test_is_safe_critical_resources(self, environment_monitor):
        """Test safety check with critical resources"""
        environment_monitor.last_assessment = {
            "threat_level": "none",
            "resource_status": "critical",
        }
        assert environment_monitor.is_safe_to_operate() is False

    def test_is_safe_healthy_conditions(self, environment_monitor):
        """Test safety check with healthy conditions"""
        environment_monitor.last_assessment = {
            "threat_level": "low",
            "resource_status": "healthy",
        }
        assert environment_monitor.is_safe_to_operate() is True


class TestContinuousMonitoring:
    """Tests for continuous monitoring"""

    @pytest.mark.asyncio
    async def test_start_monitoring(self, environment_monitor):
        """Test starting continuous monitoring"""
        assert environment_monitor.is_monitoring is False

        await environment_monitor.start_monitoring()
        assert environment_monitor.is_monitoring is True

        # Cleanup
        await environment_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, environment_monitor):
        """Test stopping monitoring"""
        await environment_monitor.start_monitoring()
        assert environment_monitor.is_monitoring is True

        await environment_monitor.stop_monitoring()
        assert environment_monitor.is_monitoring is False

    @pytest.mark.asyncio
    async def test_monitoring_loop_runs(self, environment_monitor):
        """Test monitoring loop performs assessments"""
        await environment_monitor.start_monitoring()

        # Wait for at least one assessment
        await asyncio.sleep(0.2)

        # Check assessment was performed
        assert environment_monitor.last_assessment is not None

        # Cleanup
        await environment_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_monitoring_already_active_warning(self, environment_monitor):
        """Test warning when starting already active monitoring"""
        await environment_monitor.start_monitoring()

        # Try to start again (should log warning)
        await environment_monitor.start_monitoring()

        # Cleanup
        await environment_monitor.stop_monitoring()
