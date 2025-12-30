"""
Environment Awareness - Runtime State Monitoring and Adaptation

Story 2: Environment Awareness (Epic 2.4)
Points: 4

Conscious agents must be AWARE of their environment to operate effectively.
This module provides situational awareness through:

1. Resource Monitoring - CPU, memory, disk, network utilization
2. Threat Detection - Suspicious activity, anomalies, security events
3. Neighbor Discovery - Other agents, services, and dependencies
4. Adaptive Behavior - Adjust operations based on environmental constraints

An agent with environment awareness can:
- Scale behavior based on available resources
- Detect and respond to threats in real-time
- Coordinate with neighboring agents
- Adapt to changing operational conditions
"""

import asyncio
import logging
import os
import psutil
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Environment classifications"""

    KUBERNETES = "kubernetes"
    SERVERLESS = "serverless"
    EDGE = "edge"
    DEVELOPMENT = "development"


class ThreatLevel(Enum):
    """Threat severity levels"""

    NONE = 0  # No threats detected
    LOW = 1  # Minor anomalies
    MEDIUM = 2  # Suspicious activity
    HIGH = 3  # Active threats
    CRITICAL = 4  # Immediate danger
    
    @property
    def name_str(self) -> str:
        """Get string name of threat level"""
        return {
            0: "none",
            1: "low",
            2: "medium",
            3: "high",
            4: "critical",
        }[self.value]


class ResourceStatus(Enum):
    """Resource availability status"""

    ABUNDANT = "abundant"  # >75% available
    HEALTHY = "healthy"  # 50-75% available
    CONSTRAINED = "constrained"  # 25-50% available
    CRITICAL = "critical"  # <25% available


class EnvironmentMonitor:
    """
    Monitor runtime environment for situational awareness.

    Provides real-time monitoring of:
    - System resources (CPU, memory, disk, network)
    - Threat indicators (anomalies, suspicious activity)
    - Neighboring agents (discovery and coordination)
    - Environmental constraints (limits, quotas, policies)

    Example:
        >>> monitor = EnvironmentMonitor(agent_did="did:waooaw:agent:wow-marketing")
        >>> state = await monitor.assess_environment()
        >>> print(f"Resources: {state['resource_status']}")
        >>> print(f"Threats: {state['threat_level']}")
    """

    def __init__(
        self,
        agent_did: str,
        environment_type: Optional[EnvironmentType] = None,
        monitoring_interval: float = 5.0,
    ):
        """
        Initialize environment monitor.

        Args:
            agent_did: DID of agent being monitored
            environment_type: Type of runtime environment
            monitoring_interval: Seconds between monitoring cycles
        """
        self.agent_did = agent_did
        self.environment_type = environment_type or self._detect_environment()
        self.monitoring_interval = monitoring_interval

        # State tracking
        self.is_monitoring = False
        self.last_assessment: Optional[Dict[str, Any]] = None
        self.threat_history: List[Dict[str, Any]] = []
        self.neighbors: Set[str] = set()
        self.baseline_metrics: Optional[Dict[str, float]] = None

        logger.info(
            f"Environment monitor initialized for {agent_did} "
            f"in {self.environment_type.value} environment"
        )

    def _detect_environment(self) -> EnvironmentType:
        """Detect runtime environment type"""
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return EnvironmentType.KUBERNETES
        elif os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            return EnvironmentType.SERVERLESS
        elif os.getenv("EDGE_RUNTIME"):
            return EnvironmentType.EDGE
        else:
            return EnvironmentType.DEVELOPMENT

    async def assess_environment(self) -> Dict[str, Any]:
        """
        Perform comprehensive environment assessment.

        Returns:
            Environment state dictionary with:
            - resource_status: Current resource availability
            - threat_level: Detected threat severity
            - neighbors: List of discovered agents
            - constraints: Environmental limitations
            - timestamp: Assessment time
        """
        logger.debug(f"Assessing environment for {self.agent_did}...")

        # Collect metrics
        resources = await self._assess_resources()
        threats = await self._detect_threats()
        neighbors = await self._discover_neighbors()
        constraints = await self._identify_constraints()

        # Build assessment
        assessment = {
            "agent_did": self.agent_did,
            "environment_type": self.environment_type.value,
            "resource_status": resources["status"].value,
            "resource_metrics": resources["metrics"],
            "threat_level": threats["level"].name_str,
            "threat_indicators": threats["indicators"],
            "neighbors": list(neighbors),
            "neighbor_count": len(neighbors),
            "constraints": constraints,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_active": self.is_monitoring,
        }

        # Store for historical tracking
        self.last_assessment = assessment

        # Update baseline on first assessment
        if not self.baseline_metrics:
            self.baseline_metrics = resources["metrics"].copy()

        logger.info(
            f"🌍 Environment assessed: {resources['status'].value} resources, "
            f"{threats['level'].name_str} threat level, {len(neighbors)} neighbors"
        )

        return assessment

    async def _assess_resources(self) -> Dict[str, Any]:
        """
        Assess system resource availability.

        Returns:
            Dictionary with status and metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # Network (if available)
            try:
                net_io = psutil.net_io_counters()
                network_active = net_io.bytes_sent > 0 or net_io.bytes_recv > 0
            except Exception:
                network_active = True  # Assume active if can't measure

            # Calculate overall resource availability
            avg_usage = (cpu_percent + memory_percent + disk_percent) / 3
            available = 100 - avg_usage

            # Determine status
            if available > 75:
                status = ResourceStatus.ABUNDANT
            elif available > 50:
                status = ResourceStatus.HEALTHY
            elif available > 25:
                status = ResourceStatus.CONSTRAINED
            else:
                status = ResourceStatus.CRITICAL

            return {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_percent": disk_percent,
                    "disk_available_gb": disk.free / (1024 * 1024 * 1024),
                    "network_active": network_active,
                    "overall_available": available,
                },
            }

        except Exception as e:
            logger.warning(f"Could not assess resources: {e}")
            return {
                "status": ResourceStatus.HEALTHY,
                "metrics": {
                    "cpu_percent": 50.0,
                    "memory_percent": 50.0,
                    "memory_available_mb": 1024.0,
                    "disk_percent": 50.0,
                    "disk_available_gb": 10.0,
                    "network_active": True,
                    "overall_available": 50.0,
                },
            }

    async def _detect_threats(self) -> Dict[str, Any]:
        """
        Detect environmental threats and anomalies.

        Returns:
            Dictionary with threat level and indicators
        """
        indicators = []
        threat_level = ThreatLevel.NONE

        try:
            # Check 1: Resource exhaustion (potential DoS)
            if self.last_assessment:
                prev_cpu = self.last_assessment.get("resource_metrics", {}).get(
                    "cpu_percent", 0
                )
                curr_cpu = psutil.cpu_percent(interval=0.1)

                if curr_cpu > 90:
                    indicators.append("high_cpu_usage")
                    threat_level = ThreatLevel.MEDIUM

                # Spike detection
                if prev_cpu > 0 and curr_cpu > prev_cpu * 2:
                    indicators.append("cpu_spike")
                    threat_level = ThreatLevel.LOW if threat_level.value < ThreatLevel.LOW.value else threat_level

            # Check 2: Memory pressure
            memory = psutil.virtual_memory()
            if memory.percent > 95:
                indicators.append("memory_exhaustion")
                threat_level = ThreatLevel.HIGH if threat_level.value < ThreatLevel.HIGH.value else threat_level
            elif memory.percent > 85:
                indicators.append("memory_pressure")
                threat_level = ThreatLevel.MEDIUM if threat_level.value < ThreatLevel.MEDIUM.value else threat_level

            # Check 3: Disk space critical
            disk = psutil.disk_usage("/")
            if disk.percent > 95:
                indicators.append("disk_full")
                threat_level = ThreatLevel.HIGH if threat_level.value < ThreatLevel.HIGH.value else threat_level

            # Check 4: Too many processes (fork bomb detection)
            try:
                process_count = len(psutil.pids())
                if process_count > 1000:
                    indicators.append("excessive_processes")
                    threat_level = ThreatLevel.MEDIUM if threat_level.value < ThreatLevel.MEDIUM.value else threat_level
            except Exception:
                pass

            # Store threat history
            if threat_level != ThreatLevel.NONE:
                self.threat_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": threat_level.name_str,
                        "indicators": indicators.copy(),
                    }
                )

                # Keep last 100 threats
                if len(self.threat_history) > 100:
                    self.threat_history.pop(0)

        except Exception as e:
            logger.warning(f"Could not detect threats: {e}")

        return {"level": threat_level, "indicators": indicators}

    async def _discover_neighbors(self) -> Set[str]:
        """
        Discover neighboring agents and services.

        Returns:
            Set of neighbor DIDs
        """
        neighbors = set()

        try:
            # In Kubernetes: query pods in same namespace
            if self.environment_type == EnvironmentType.KUBERNETES:
                namespace = os.getenv("POD_NAMESPACE", "default")
                # TODO: Actual k8s API query
                # For now, simulate with environment variables
                neighbor_list = os.getenv("AGENT_NEIGHBORS", "").split(",")
                neighbors.update([n.strip() for n in neighbor_list if n.strip()])

            # In serverless: check concurrent executions
            elif self.environment_type == EnvironmentType.SERVERLESS:
                # Neighbors are other function instances
                # TODO: Query Lambda API for concurrent executions
                pass

            # In development: check other processes
            elif self.environment_type == EnvironmentType.DEVELOPMENT:
                # Look for other Python processes (simulated agents)
                for proc in psutil.process_iter(["name", "cmdline"]):
                    try:
                        if "python" in proc.info["name"].lower():
                            cmdline = proc.info.get("cmdline", [])
                            # Check if running another agent
                            if any("agent" in str(arg).lower() for arg in cmdline):
                                # Extract DID if present
                                for arg in cmdline:
                                    if "did:waooaw:" in str(arg):
                                        neighbors.add(str(arg))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

        except Exception as e:
            logger.debug(f"Could not discover neighbors: {e}")

        # Update stored neighbors
        self.neighbors = neighbors
        return neighbors

    async def _identify_constraints(self) -> Dict[str, Any]:
        """
        Identify environmental constraints and limits.

        Returns:
            Dictionary of constraints
        """
        constraints = {
            "cpu_limit": None,
            "memory_limit_mb": None,
            "disk_quota_gb": None,
            "network_bandwidth_mbps": None,
            "concurrent_operations": None,
        }

        try:
            # Kubernetes resource limits
            if self.environment_type == EnvironmentType.KUBERNETES:
                # Read from cgroup limits
                try:
                    # CPU limit
                    with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", "r") as f:
                        quota = int(f.read())
                        if quota > 0:
                            with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us", "r") as p:
                                period = int(p.read())
                                constraints["cpu_limit"] = quota / period
                except Exception:
                    pass

                # Memory limit
                try:
                    with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as f:
                        limit = int(f.read())
                        constraints["memory_limit_mb"] = limit / (1024 * 1024)
                except Exception:
                    pass

            # Serverless limits
            elif self.environment_type == EnvironmentType.SERVERLESS:
                # AWS Lambda limits
                constraints["memory_limit_mb"] = int(
                    os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "1024")
                )
                constraints["concurrent_operations"] = int(
                    os.getenv("AWS_LAMBDA_CONCURRENT_EXECUTIONS", "100")
                )

        except Exception as e:
            logger.debug(f"Could not identify constraints: {e}")

        return constraints

    async def start_monitoring(self):
        """Start continuous environment monitoring"""
        if self.is_monitoring:
            logger.warning(f"Monitoring already active for {self.agent_did}")
            return

        self.is_monitoring = True
        logger.info(f"🔍 Starting environment monitoring for {self.agent_did}")

        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        logger.info(f"⏸️  Stopped environment monitoring for {self.agent_did}")

    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.is_monitoring:
            try:
                await self.assess_environment()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def get_adaptive_recommendations(self) -> Dict[str, Any]:
        """
        Generate adaptive behavior recommendations based on environment.

        Returns:
            Dictionary of recommendations for adapting behavior
        """
        if not self.last_assessment:
            return {"recommendations": [], "reason": "No assessment available"}

        recommendations = []
        resource_status = self.last_assessment["resource_status"]
        threat_level = self.last_assessment["threat_level"]

        # Resource-based recommendations
        if resource_status == "critical":
            recommendations.extend(
                [
                    "reduce_concurrency",
                    "pause_non_essential_tasks",
                    "enable_aggressive_caching",
                    "defer_heavy_operations",
                ]
            )
        elif resource_status == "constrained":
            recommendations.extend(
                ["limit_concurrency", "enable_caching", "optimize_queries"]
            )
        elif resource_status == "abundant":
            recommendations.extend(
                ["increase_concurrency", "precompute_results", "aggressive_prefetch"]
            )

        # Threat-based recommendations
        if threat_level == "critical":
            recommendations.extend(["enable_defense_mode", "rate_limit_aggressively"])
        elif threat_level == "high":
            recommendations.extend(["increase_validation", "enable_audit_logging"])
        elif threat_level == "medium":
            recommendations.append("monitor_closely")

        # Neighbor-based recommendations
        neighbor_count = self.last_assessment["neighbor_count"]
        if neighbor_count > 10:
            recommendations.append("enable_coordination")
        elif neighbor_count == 0:
            recommendations.append("operate_independently")

        return {
            "recommendations": recommendations,
            "resource_status": resource_status,
            "threat_level": threat_level,
            "neighbor_count": neighbor_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def is_safe_to_operate(self) -> bool:
        """
        Check if environment is safe for normal operations.

        Returns:
            True if safe to operate, False if should pause/shutdown
        """
        if not self.last_assessment:
            return True  # Assume safe if no assessment yet

        # Check threats
        threat_level = self.last_assessment["threat_level"]
        if threat_level == "critical":
            return False

        # Check resources
        resource_status = self.last_assessment["resource_status"]
        if resource_status == "critical":
            return False

        return True
