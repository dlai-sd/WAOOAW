"""
Agent Servicing State Management
Story 5.1.11: Zero-downtime agent upgrades with rollback
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class AgentForUpgrade:
    """Agent available for servicing/upgrade"""
    agent_id: str
    name: str
    category: str
    current_version: str
    status: str
    health: str
    uptime_days: int


@dataclass
class AgentVersion:
    """Agent version information"""
    version_id: str
    version: str
    release_date: str
    status: str  # current, available, deprecated
    changelog: str
    size_mb: float
    is_current: bool = False
    is_recommended: bool = False


@dataclass
class DeploymentStrategy:
    """Deployment strategy configuration"""
    strategy_id: str
    name: str
    description: str
    icon: str
    estimated_time: str
    risk_level: str  # low, medium, high
    supports_rollback: bool
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result"""
    check_id: str
    name: str
    status: str  # pass, fail, warning
    message: str
    timestamp: str
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    latency_increase: Optional[float] = None


@dataclass
class UpgradeStep:
    """Upgrade wizard step"""
    step_name: str
    status: str  # pending, running, completed, failed
    message: str
    timestamp: str
    duration_sec: Optional[float] = None


@dataclass
class UpgradeHistory:
    """Historical upgrade record"""
    upgrade_id: str
    agent_id: str
    agent_name: str
    from_version: str
    to_version: str
    strategy: str
    status: str  # completed, failed, rolled_back
    start_time: str
    end_time: str
    duration_min: float
    performed_by: str


class ServicingState(rx.State):
    """State management for agent servicing and upgrades"""
    
    # Wizard state
    current_step: int = 0  # 0-5 for 6 steps
    
    # Agent selection
    agents: List[AgentForUpgrade] = []
    selected_agents: List[str] = []
    
    # Version management
    available_versions: List[AgentVersion] = []
    selected_version: Optional[str] = None
    
    # Deployment strategy
    strategies: List[DeploymentStrategy] = []
    selected_strategy: Optional[str] = None
    strategy_config: Dict[str, Any] = {}
    
    # Backup
    backup_enabled: bool = True
    backup_location: str = "s3://waooaw-backups/agents/"
    backup_status: str = "pending"  # pending, in_progress, completed, failed
    
    # Health monitoring
    health_checks: List[HealthCheck] = []
    health_status: str = "unknown"  # healthy, degraded, unhealthy
    auto_rollback_enabled: bool = True
    
    # Upgrade progress
    upgrade_steps: List[UpgradeStep] = []
    is_upgrading: bool = False
    upgrade_complete: bool = False
    upgrade_success: bool = False
    
    # Rollback
    can_rollback: bool = False
    rollback_in_progress: bool = False
    
    # Configuration patching
    config_patches: Dict[str, Any] = {}
    config_patches_json: str = ""
    config_validation_error: str = ""
    
    # History
    upgrade_history: List[UpgradeHistory] = []
    
    def load_agents(self):
        """Load agents available for servicing"""
        self.agents = [
            AgentForUpgrade(
                agent_id="agent-001",
                name="Content Writer AI",
                category="marketing",
                current_version="v2.3.0",
                status="running",
                health="healthy",
                uptime_days=45,
            ),
            AgentForUpgrade(
                agent_id="agent-002",
                name="Math Tutor Pro",
                category="education",
                current_version="v1.8.2",
                status="running",
                health="healthy",
                uptime_days=120,
            ),
            AgentForUpgrade(
                agent_id="agent-003",
                name="SDR Agent Alpha",
                category="sales",
                current_version="v3.1.0",
                status="running",
                health="degraded",
                uptime_days=12,
            ),
            AgentForUpgrade(
                agent_id="agent-004",
                name="Social Media Manager",
                category="marketing",
                current_version="v2.0.1",
                status="running",
                health="healthy",
                uptime_days=89,
            ),
            AgentForUpgrade(
                agent_id="agent-005",
                name="Science Lab Assistant",
                category="education",
                current_version="v1.5.4",
                status="stopped",
                health="unknown",
                uptime_days=0,
            ),
        ]
    
    def load_versions(self):
        """Load available agent versions"""
        self.available_versions = [
            AgentVersion(
                version_id="v3.2.0",
                version="v3.2.0",
                release_date="2026-01-10",
                status="available",
                changelog="Performance improvements, bug fixes, new ML model",
                size_mb=245.8,
                is_recommended=True,
            ),
            AgentVersion(
                version_id="v3.1.0",
                version="v3.1.0",
                release_date="2025-12-15",
                status="current",
                changelog="Feature enhancements, security updates",
                size_mb=238.2,
                is_current=True,
            ),
            AgentVersion(
                version_id="v3.0.5",
                version="v3.0.5",
                release_date="2025-11-20",
                status="available",
                changelog="Stability improvements, minor bug fixes",
                size_mb=235.1,
            ),
            AgentVersion(
                version_id="v2.9.2",
                version="v2.9.2",
                release_date="2025-10-01",
                status="deprecated",
                changelog="Legacy version, security patches only",
                size_mb=220.5,
            ),
        ]
    
    def load_strategies(self):
        """Load deployment strategies"""
        self.strategies = [
            DeploymentStrategy(
                strategy_id="blue-green",
                name="Blue-Green Deployment",
                description="Deploy new version alongside old, switch traffic instantly",
                icon="🔵🟢",
                estimated_time="8-12 min",
                risk_level="low",
                supports_rollback=True,
                config={
                    "traffic_switch_mode": "instant",
                    "keep_old_version": True,
                    "validation_period_sec": 300,
                },
            ),
            DeploymentStrategy(
                strategy_id="canary",
                name="Canary Deployment",
                description="Gradual rollout: 10% → 50% → 100% with monitoring",
                icon="🐤",
                estimated_time="15-25 min",
                risk_level="low",
                supports_rollback=True,
                config={
                    "phase1_traffic": 10,
                    "phase2_traffic": 50,
                    "phase3_traffic": 100,
                    "phase_duration_min": 5,
                    "auto_promote": True,
                },
            ),
            DeploymentStrategy(
                strategy_id="rolling",
                name="Rolling Update",
                description="Update instances one-by-one, minimize resource usage",
                icon="🔄",
                estimated_time="10-15 min",
                risk_level="medium",
                supports_rollback=True,
                config={
                    "batch_size": 1,
                    "wait_between_batches_sec": 60,
                    "health_check_interval_sec": 30,
                },
            ),
        ]
    
    def load_history(self):
        """Load upgrade history"""
        self.upgrade_history = [
            UpgradeHistory(
                upgrade_id="upg-001",
                agent_id="agent-001",
                agent_name="Content Writer AI",
                from_version="v2.2.0",
                to_version="v2.3.0",
                strategy="blue-green",
                status="completed",
                start_time="2026-01-10 08:15:00",
                end_time="2026-01-10 08:24:00",
                duration_min=9.0,
                performed_by="admin@waooaw.com",
            ),
            UpgradeHistory(
                upgrade_id="upg-002",
                agent_id="agent-003",
                agent_name="SDR Agent Alpha",
                from_version="v3.0.5",
                to_version="v3.1.0",
                strategy="canary",
                status="completed",
                start_time="2026-01-12 14:30:00",
                end_time="2026-01-12 14:52:00",
                duration_min=22.0,
                performed_by="admin@waooaw.com",
            ),
            UpgradeHistory(
                upgrade_id="upg-003",
                agent_id="agent-002",
                agent_name="Math Tutor Pro",
                from_version="v1.8.0",
                to_version="v1.8.2",
                strategy="rolling",
                status="rolled_back",
                start_time="2026-01-08 10:00:00",
                end_time="2026-01-08 10:28:00",
                duration_min=28.0,
                performed_by="admin@waooaw.com",
            ),
        ]
    
    def toggle_agent_selection(self, agent_id: str):
        """Toggle agent selection"""
        if agent_id in self.selected_agents:
            self.selected_agents.remove(agent_id)
        else:
            self.selected_agents.append(agent_id)
    
    def is_agent_selected(self, agent_id: str) -> bool:
        """Check if agent is selected"""
        return agent_id in self.selected_agents
    
    def select_version(self, version_id: str):
        """Select target version"""
        self.selected_version = version_id
    
    def select_strategy(self, strategy_id: str):
        """Select deployment strategy"""
        self.selected_strategy = strategy_id
        # Load default config for strategy
        strategy = next((s for s in self.strategies if s.strategy_id == strategy_id), None)
        if strategy:
            self.strategy_config = strategy.config.copy()
    
    def update_strategy_config(self, key: str, value: Any):
        """Update strategy configuration"""
        self.strategy_config[key] = value
    
    def next_step(self):
        """Move to next wizard step"""
        if self.current_step < 5:
            self.current_step += 1
    
    def previous_step(self):
        """Move to previous wizard step"""
        if self.current_step > 0:
            self.current_step -= 1
    
    async def create_backup(self):
        """Create agent backup"""
        self.backup_status = "in_progress"
        yield
        
        # Simulate backup process
        import asyncio
        await asyncio.sleep(2)
        
        self.backup_status = "completed"
        self.can_rollback = True
    
    async def run_health_checks(self):
        """Run pre-upgrade health checks"""
        self.health_checks = []
        
        checks = [
            ("API Endpoint", "pass", "All endpoints responding normally", 45.2, 0.1, 0.0),
            ("Database Connection", "pass", "Connection pool healthy", 12.5, 0.0, 0.0),
            ("Memory Usage", "pass", "Within normal limits (65%)", 8.1, 0.0, 0.0),
            ("CPU Load", "warning", "Slightly elevated (78%)", 15.3, 0.0, 5.2),
            ("Error Rate", "pass", "Below threshold (0.8%)", 22.0, 0.8, 0.0),
        ]
        
        for name, status, message, response_time, error_rate, latency in checks:
            self.health_checks.append(
                HealthCheck(
                    check_id=f"check-{len(self.health_checks)}",
                    name=name,
                    status=status,
                    message=message,
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    response_time_ms=response_time,
                    error_rate=error_rate,
                    latency_increase=latency,
                )
            )
            yield
            
            # Simulate check execution
            import asyncio
            await asyncio.sleep(0.5)
        
        # Determine overall health
        failed = sum(1 for c in self.health_checks if c.status == "fail")
        warnings = sum(1 for c in self.health_checks if c.status == "warning")
        
        if failed > 0:
            self.health_status = "unhealthy"
        elif warnings > 0:
            self.health_status = "degraded"
        else:
            self.health_status = "healthy"
    
    async def start_upgrade(self):
        """Start the upgrade process"""
        self.is_upgrading = True
        self.upgrade_complete = False
        self.upgrade_success = False
        self.upgrade_steps = []
        yield
        
        # Step 1: Pre-flight checks
        await self._add_upgrade_step("Pre-flight Checks", "Validating environment and prerequisites")
        yield
        
        # Step 2: Deploy new version
        await self._add_upgrade_step("Deploy New Version", "Pulling image and starting new containers")
        yield
        
        # Step 3: Health validation
        await self._add_upgrade_step("Health Validation", "Running health checks on new version")
        yield
        
        # Step 4: Traffic cutover
        strategy = next((s for s in self.strategies if s.strategy_id == self.selected_strategy), None)
        if strategy and strategy.strategy_id == "canary":
            await self._add_upgrade_step("Cutover Phase 1", "Routing 10% of traffic to new version")
            yield
            await self._add_upgrade_step("Cutover Phase 2", "Routing 50% of traffic to new version")
            yield
            await self._add_upgrade_step("Cutover Phase 3", "Routing 100% of traffic to new version")
            yield
        else:
            await self._add_upgrade_step("Traffic Cutover", "Switching all traffic to new version")
            yield
        
        # Step 5: Post-upgrade validation
        await self._add_upgrade_step("Post-Upgrade Validation", "Monitoring new version performance")
        yield
        
        # Step 6: Cleanup
        await self._add_upgrade_step("Cleanup", "Removing old version containers")
        yield
        
        self.is_upgrading = False
        self.upgrade_complete = True
        self.upgrade_success = True
    
    async def _add_upgrade_step(self, step_name: str, message: str):
        """Add upgrade step with simulated execution"""
        import asyncio
        
        # Add step as running
        step = UpgradeStep(
            step_name=step_name,
            status="running",
            message=message,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
        self.upgrade_steps.append(step)
        
        # Simulate execution time (2-4 seconds)
        await asyncio.sleep(3)
        
        # Mark as completed
        self.upgrade_steps[-1].status = "completed"
        self.upgrade_steps[-1].duration_sec = 3.0
    
    async def trigger_rollback(self):
        """Trigger automatic rollback"""
        self.rollback_in_progress = True
        self.is_upgrading = False
        yield
        
        # Add rollback steps
        await self._add_upgrade_step("Rollback Initiated", "Reverting to previous version")
        yield
        await self._add_upgrade_step("Traffic Switch", "Routing traffic back to old version")
        yield
        await self._add_upgrade_step("Health Check", "Verifying old version is healthy")
        yield
        
        self.rollback_in_progress = False
        self.upgrade_complete = True
        self.upgrade_success = False
    
    def update_config_patch(self, key: str, value: Any):
        """Update configuration patch"""
        self.config_patches[key] = value
    
    def set_config_patches_json(self, value: str):
        """Update config patches JSON string"""
        self.config_patches_json = value
        self.config_validation_error = ""
    
    def validate_config_patches(self):
        """Validate configuration patches JSON"""
        import json
        try:
            if self.config_patches_json.strip():
                self.config_patches = json.loads(self.config_patches_json)
                self.config_validation_error = ""
            else:
                self.config_patches = {}
                self.config_validation_error = ""
        except json.JSONDecodeError as e:
            self.config_validation_error = f"Invalid JSON: {str(e)}"
    
    def clear_config_patches(self):
        """Clear configuration patches"""
        self.config_patches = {}
        self.config_patches_json = ""
        self.config_validation_error = ""
    
    def apply_config_patches(self):
        """Apply configuration patches without restart"""
        # In real implementation, this would hot-reload agent configs
        return True
    
    def reset_wizard(self):
        """Reset wizard to start"""
        self.current_step = 0
        self.selected_agents = []
        self.selected_version = None
        self.selected_strategy = None
        self.strategy_config = {}
        self.backup_status = "pending"
        self.health_checks = []
        self.health_status = "unknown"
        self.upgrade_steps = []
        self.is_upgrading = False
        self.upgrade_complete = False
        self.upgrade_success = False
        self.can_rollback = False
        self.rollback_in_progress = False
        self.config_patches = {}
    
    @rx.var
    def can_proceed(self) -> bool:
        """Check if can proceed to next step"""
        if self.current_step == 0:
            # Step 1: Must select agents and version
            return len(self.selected_agents) > 0 and self.selected_version is not None
        elif self.current_step == 1:
            # Step 2: Backup must be completed
            return self.backup_status == "completed"
        elif self.current_step == 2:
            # Step 3: Must select strategy
            return self.selected_strategy is not None
        elif self.current_step == 3:
            # Step 4: Health checks must pass
            return self.health_status in ["healthy", "degraded"]
        elif self.current_step == 4:
            # Step 5: Upgrade must complete
            return self.upgrade_complete
        else:
            return True
    
    @rx.var
    def progress_percentage(self) -> int:
        """Calculate wizard progress percentage"""
        return int((self.current_step / 5) * 100)
    
    @rx.var
    def selected_agent_count(self) -> int:
        """Count of selected agents"""
        return len(self.selected_agents)
    
    @rx.var
    def validation_period_sec(self) -> int:
        """Get validation period from strategy config"""
        return self.strategy_config.get("validation_period_sec", 300)
    
    @rx.var
    def keep_old_version(self) -> bool:
        """Get keep old version setting"""
        return self.strategy_config.get("keep_old_version", True)
    
    @rx.var
    def phase1_traffic(self) -> int:
        """Get phase 1 traffic percentage"""
        return self.strategy_config.get("phase1_traffic", 10)
    
    @rx.var
    def phase2_traffic(self) -> int:
        """Get phase 2 traffic percentage"""
        return self.strategy_config.get("phase2_traffic", 50)
    
    @rx.var
    def phase3_traffic(self) -> int:
        """Get phase 3 traffic percentage"""
        return self.strategy_config.get("phase3_traffic", 100)
    
    @rx.var
    def phase_duration_min(self) -> int:
        """Get phase duration in minutes"""
        return self.strategy_config.get("phase_duration_min", 5)
    
    @rx.var
    def batch_size(self) -> int:
        """Get batch size for rolling updates"""
        return self.strategy_config.get("batch_size", 1)
    
    @rx.var
    def wait_between_batches_sec(self) -> int:
        """Get wait time between batches"""
        return self.strategy_config.get("wait_between_batches_sec", 60)
    
    @rx.var
    def has_health_checks(self) -> bool:
        """Check if health checks exist"""
        return len(self.health_checks) > 0
    
    @rx.var
    def upgrade_progress_percent(self) -> int:
        """Calculate upgrade progress percentage"""
        if len(self.upgrade_steps) == 0:
            return 0
        return int((len(self.upgrade_steps) / 6) * 100)

