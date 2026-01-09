#!/usr/bin/env python3
"""
WAOOAW Platform Simulation Script
Version: 1.0
Purpose: End-to-end simulation of customer and platform portal journeys
Reference: grooming_lifecycle_blueprint.md, CP_USER_JOURNEY.yaml, PP_USER_JOURNEY.yaml
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


# =============================================================================
# SIMULATION CONFIGURATION
# =============================================================================

class SimulationMode(Enum):
    """Simulation modes"""
    FULL = "full"  # All scenarios
    TRIAL_ONLY = "trial_only"  # Just trial lifecycle
    PLATFORM_PORTAL = "platform_portal"  # Just PP scenarios
    QUICK = "quick"  # Fast validation (skip delays)


@dataclass
class SimulationConfig:
    """Simulation configuration"""
    mode: SimulationMode = SimulationMode.FULL
    enable_delays: bool = True  # Simulate real-world timing
    enable_failures: bool = True  # Test failure scenarios
    verbose: bool = True  # Print detailed logs
    base_url: str = "http://localhost:8015"  # PP Gateway
    admin_url: str = "http://localhost:8006"  # Admin Gateway


# =============================================================================
# MOCK SERVICES (Simulate Backend Services)
# =============================================================================

class MockAgentStatus(Enum):
    """Agent status states"""
    TRIAL_PENDING = "trial_pending"
    TRIAL_PROVISIONING = "trial_provisioning"
    TRIAL_ACTIVE = "trial_active"
    TRIAL_GO_LIVE_PENDING = "trial_go_live_pending"
    PRODUCTION_ACTIVE = "production_active"
    TRIAL_EXPIRED = "trial_expired"
    TRIAL_CANCELLED = "trial_cancelled"
    TRIAL_FAILED = "trial_failed"


@dataclass
class MockAgent:
    """Mock agent object"""
    agent_id: str
    customer_id: str
    status: MockAgentStatus
    industry: str
    specialty: str
    oauth_credentials: List[str]
    goals: List[str]
    created_at: datetime
    trial_ends_at: Optional[datetime] = None
    certification_passed: bool = False


@dataclass
class MockCustomer:
    """Mock customer object"""
    customer_id: str
    email: str
    role: str  # "governor", "manager", "worker"
    device_token: Optional[str] = None  # For FCM push
    created_at: datetime = datetime.utcnow()


@dataclass
class MockApprovalRequest:
    """Mock approval request"""
    approval_id: str
    agent_id: str
    action_type: str
    action_details: Dict
    status: str  # "pending", "approved", "rejected", "expired"
    created_at: datetime


class MockDatabase:
    """In-memory database for simulation"""
    
    def __init__(self):
        self.agents: Dict[str, MockAgent] = {}
        self.customers: Dict[str, MockCustomer] = {}
        self.approvals: Dict[str, MockApprovalRequest] = {}
        self.audit_logs: List[Dict] = []
        self.incidents: List[Dict] = []
        self.tickets: List[Dict] = []
    
    def create_customer(self, customer: MockCustomer):
        """Create customer"""
        self.customers[customer.customer_id] = customer
        self._audit_log("customer_created", {"customer_id": customer.customer_id})
    
    def create_agent(self, agent: MockAgent):
        """Create agent"""
        self.agents[agent.agent_id] = agent
        self._audit_log("agent_created", {"agent_id": agent.agent_id})
    
    def update_agent_status(self, agent_id: str, new_status: MockAgentStatus):
        """Update agent status"""
        if agent_id in self.agents:
            old_status = self.agents[agent_id].status
            self.agents[agent_id].status = new_status
            self._audit_log("agent_status_changed", {
                "agent_id": agent_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
            })
    
    def create_approval(self, approval: MockApprovalRequest):
        """Create approval request"""
        self.approvals[approval.approval_id] = approval
        self._audit_log("approval_request_created", {
            "approval_id": approval.approval_id,
            "agent_id": approval.agent_id,
        })
    
    def approve_action(self, approval_id: str):
        """Approve action"""
        if approval_id in self.approvals:
            self.approvals[approval_id].status = "approved"
            self._audit_log("approval_granted", {"approval_id": approval_id})
    
    def create_incident(self, incident: Dict):
        """Create incident"""
        self.incidents.append(incident)
        self._audit_log("incident_created", incident)
    
    def create_ticket(self, ticket: Dict):
        """Create ticket"""
        self.tickets.append(ticket)
        self._audit_log("ticket_created", ticket)
    
    def _audit_log(self, event_type: str, event_data: Dict):
        """Append audit log"""
        self.audit_logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "event_data": event_data,
        })
    
    def get_audit_logs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Query audit logs"""
        if not filters:
            return self.audit_logs
        
        # Simple filtering (agent_id, customer_id, event_type)
        filtered = self.audit_logs
        if "agent_id" in filters:
            filtered = [log for log in filtered if filters["agent_id"] in str(log.get("event_data", {}))]
        if "event_type" in filters:
            filtered = [log for log in filtered if log["event_type"] == filters["event_type"]]
        return filtered


# =============================================================================
# SIMULATION ENGINE
# =============================================================================

class SimulationEngine:
    """Main simulation engine"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.db = MockDatabase()
        self.start_time = time.time()
    
    async def run(self):
        """Run simulation"""
        print(f"\n{'='*80}")
        print(f"WAOOAW Platform Simulation - Mode: {self.config.mode.value}")
        print(f"{'='*80}\n")
        
        if self.config.mode in [SimulationMode.FULL, SimulationMode.TRIAL_ONLY]:
            await self.scenario_cp_trial_lifecycle()
            await self.scenario_cp_setup_wizard()
            await self.scenario_cp_mobile_approval()
            await self.scenario_cp_go_live()
        
        if self.config.mode in [SimulationMode.FULL, SimulationMode.PLATFORM_PORTAL]:
            await self.scenario_pp_health_monitoring()
            await self.scenario_pp_audit_query()
            await self.scenario_pp_support_ticket()
            await self.scenario_pp_deployment()
        
        if self.config.mode == SimulationMode.FULL:
            await self.scenario_config_update_propagation()
            await self.scenario_oauth_token_refresh()
            await self.scenario_incident_response()
        
        await self.print_summary()
    
    # =========================================================================
    # CUSTOMER PORTAL SCENARIOS (FLOW-CP-*)
    # =========================================================================
    
    async def scenario_cp_trial_lifecycle(self):
        """
        Scenario: FLOW-CP-TRIAL-001 - Trial Start & Provisioning
        Reference: flow_definitions.yml → FLOW-CP-TRIAL-001
        Duration: 5-10 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: CP Trial Lifecycle (FLOW-CP-TRIAL-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Customer registers
        customer = MockCustomer(
            customer_id="cust_001",
            email="john@example.com",
            role="governor",
            device_token="fcm_token_abc123",
        )
        self.db.create_customer(customer)
        self._log("✅ Customer registered: john@example.com")
        await self._delay(1)
        
        # Step 2: Customer initiates trial (S1: Start Trial)
        agent = MockAgent(
            agent_id="agent_001",
            customer_id=customer.customer_id,
            status=MockAgentStatus.TRIAL_PENDING,
            industry="marketing",
            specialty="content_marketing",
            oauth_credentials=[],
            goals=[],
            created_at=datetime.utcnow(),
            trial_ends_at=datetime.utcnow() + timedelta(days=7),
        )
        self.db.create_agent(agent)
        self._log("✅ Trial initiated: agent_001 (status: trial_pending)")
        await self._delay(2)
        
        # Step 3: Plant Orchestrator provisions agent (S1.1: Conceive → Birth)
        self.db.update_agent_status(agent.agent_id, MockAgentStatus.TRIAL_PROVISIONING)
        self._log("⏳ Plant Orchestrator provisioning agent...")
        await self._delay(3)
        
        # Step 4: Agent resources allocated
        self.db.update_agent_status(agent.agent_id, MockAgentStatus.TRIAL_ACTIVE)
        self._log("✅ Agent provisioned: agent_001 (status: trial_active)")
        self._log(f"   Trial ends: {agent.trial_ends_at.strftime('%Y-%m-%d %H:%M')}")
        await self._delay(1)
        
        # Step 5: Customer receives welcome email
        self._log("📧 Email sent: Welcome to WAOOAW! Your agent is ready.")
        
        print("\n✅ Scenario Complete: Trial provisioned in 7 seconds (simulated)")
        print(f"   - Customer: {customer.customer_id}")
        print(f"   - Agent: {agent.agent_id}")
        print(f"   - Status: {agent.status.value}")
    
    async def scenario_cp_setup_wizard(self):
        """
        Scenario: FLOW-CP-SETUP-001 - Setup Wizard (5-Step)
        Reference: flow_definitions.yml → FLOW-CP-SETUP-001
        Duration: 5-7 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: CP Setup Wizard (FLOW-CP-SETUP-001)")
        print(f"{'='*80}\n")
        
        agent = self.db.agents["agent_001"]
        customer = self.db.customers["cust_001"]
        
        # Step 1: Personalization (industry, specialty)
        self._log("📝 Step 1/5: Personalization")
        self._log(f"   Industry: {agent.industry}")
        self._log(f"   Specialty: {agent.specialty}")
        await self._delay(1)
        
        # Step 2: OAuth credentials (WordPress, Mailchimp)
        self._log("🔐 Step 2/5: OAuth Credentials")
        self._log("   Connecting to WordPress...")
        await self._delay(2)
        agent.oauth_credentials.append("wordpress")
        self._log("   ✅ WordPress connected")
        
        self._log("   Connecting to Mailchimp...")
        await self._delay(2)
        agent.oauth_credentials.append("mailchimp")
        self._log("   ✅ Mailchimp connected")
        
        # Step 3: Goals & objectives
        self._log("🎯 Step 3/5: Goals & Objectives")
        agent.goals.append("Publish 5 blog posts per week")
        agent.goals.append("Send 2 email campaigns per month")
        self._log(f"   Goal 1: {agent.goals[0]}")
        self._log(f"   Goal 2: {agent.goals[1]}")
        await self._delay(1)
        
        # Step 4: Approval mode setup
        self._log("✋ Step 4/5: Approval Mode")
        self._log("   Mode: Manual approval required for all external actions")
        self._log(f"   Device token: {customer.device_token}")
        await self._delay(1)
        
        # Step 5: Agent activated
        self._log("🚀 Step 5/5: Activation")
        self._log("   Agent transitioning from embryonic → active...")
        await self._delay(2)
        self._log("   ✅ Agent activated!")
        
        print("\n✅ Scenario Complete: Setup wizard completed in 9 seconds (simulated)")
        print(f"   - OAuth: {', '.join(agent.oauth_credentials)}")
        print(f"   - Goals: {len(agent.goals)}")
    
    async def scenario_cp_mobile_approval(self):
        """
        Scenario: FLOW-CP-APPROVAL-001 - Mobile Approval Workflow
        Reference: flow_definitions.yml → FLOW-CP-APPROVAL-001
        Duration: 2-5 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: CP Mobile Approval (FLOW-CP-APPROVAL-001)")
        print(f"{'='*80}\n")
        
        agent = self.db.agents["agent_001"]
        customer = self.db.customers["cust_001"]
        
        # Step 1: Agent requests approval
        approval = MockApprovalRequest(
            approval_id="approval_001",
            agent_id=agent.agent_id,
            action_type="wordpress_publish",
            action_details={
                "title": "10 Ways to Boost Your Marketing ROI",
                "content": "In today's competitive market...",
                "url": "https://example.com/blog/boost-roi",
            },
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.create_approval(approval)
        self._log("📱 Agent requested approval: Publish blog post to WordPress")
        self._log(f"   Title: {approval.action_details['title']}")
        await self._delay(1)
        
        # Step 2: Mobile push notification sent
        self._log(f"📲 FCM push sent to device: {customer.device_token}")
        self._log("   Notification: 'Agent needs approval to publish blog post'")
        await self._delay(2)
        
        # Step 3: Governor reviews action
        self._log("👀 Governor reviewing action on mobile app...")
        await self._delay(3)
        
        # Step 4: Governor approves
        self.db.approve_action(approval.approval_id)
        self._log("✅ Governor approved action")
        await self._delay(1)
        
        # Step 5: Agent resumes execution
        self._log("🚀 Agent resumed: Publishing blog post...")
        await self._delay(2)
        self._log("✅ Blog post published successfully!")
        
        print("\n✅ Scenario Complete: Approval workflow completed in 9 seconds (simulated)")
        print(f"   - Approval ID: {approval.approval_id}")
        print(f"   - Action: {approval.action_type}")
        print(f"   - Status: {approval.status}")
    
    async def scenario_cp_go_live(self):
        """
        Scenario: FLOW-CP-GO-LIVE-001 - Trial to Production Transition
        Reference: flow_definitions.yml → FLOW-CP-GO-LIVE-001
        Duration: 10-15 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: CP Go Live (FLOW-CP-GO-LIVE-001)")
        print(f"{'='*80}\n")
        
        agent = self.db.agents["agent_001"]
        
        # Step 1: Customer initiates go-live
        self._log("🚀 Customer initiated go-live request")
        self.db.update_agent_status(agent.agent_id, MockAgentStatus.TRIAL_GO_LIVE_PENDING)
        await self._delay(1)
        
        # Step 2: Genesis re-certification (42 checks)
        self._log("🔍 Genesis re-certification started...")
        self._log("   Running 42 constitutional checks...")
        await self._delay(5)
        agent.certification_passed = True
        self._log("   ✅ All 42 checks passed!")
        await self._delay(1)
        
        # Step 3: Governor approval (payment)
        self._log("💳 Governor approval: Payment required")
        self._log("   Redirecting to Stripe checkout...")
        await self._delay(3)
        self._log("   ✅ Payment successful: ₹12,000/month")
        await self._delay(1)
        
        # Step 4: Policy flip (trial → production)
        self._log("⚙️  Policy flip: trial_mode → production_mode")
        self._log("   Updating OPA policies...")
        await self._delay(2)
        self._log("   ✅ Sandbox routing disabled, production APIs enabled")
        await self._delay(1)
        
        # Step 5: Agent activated in production
        self.db.update_agent_status(agent.agent_id, MockAgentStatus.PRODUCTION_ACTIVE)
        self._log("🎉 Agent activated in production!")
        self._log(f"   Status: {agent.status.value}")
        
        print("\n✅ Scenario Complete: Go-live completed in 13 seconds (simulated)")
        print(f"   - Agent: {agent.agent_id}")
        print(f"   - Status: {agent.status.value}")
        print(f"   - Certification: Passed")
    
    # =========================================================================
    # PLATFORM PORTAL SCENARIOS (FLOW-PP-*)
    # =========================================================================
    
    async def scenario_pp_health_monitoring(self):
        """
        Scenario: FLOW-PP-HEALTH-001 - Platform Health Monitoring
        Reference: flow_definitions.yml → FLOW-PP-HEALTH-001
        Duration: Continuous (real-time)
        """
        print(f"\n{'='*80}")
        print("SCENARIO: PP Health Monitoring (FLOW-PP-HEALTH-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Health Aggregator collects metrics
        self._log("📊 Health Aggregator collecting metrics...")
        services = [
            ("Agent Execution", 8002, "healthy", 45),
            ("Governance", 8003, "healthy", 120),
            ("Customer Service", 8004, "healthy", 80),
            ("ML Inference", 8005, "degraded", 350),  # High latency!
            ("Orchestration", 8001, "healthy", 60),
        ]
        
        for service_name, port, status, latency in services:
            self._log(f"   {service_name} (:{port}): {status} ({latency}ms)")
        
        await self._delay(2)
        
        # Step 2: Anomaly detection (ML Inference slow)
        self._log("🚨 Anomaly detected: ML Inference latency >300ms")
        self._log("   Expected: <200ms, Actual: 350ms")
        await self._delay(1)
        
        # Step 3: Create incident
        incident = {
            "incident_id": "incident_001",
            "severity": "warning",
            "service": "ML Inference (8005)",
            "description": "High latency detected",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.db.create_incident(incident)
        self._log(f"📋 Incident created: {incident['incident_id']}")
        await self._delay(1)
        
        # Step 4: Alert Systems Architect
        self._log("📧 Alert sent to Systems Architect Agent")
        await self._delay(1)
        
        # Step 5: Auto-recovery (scale Cloud Run)
        self._log("🔧 Auto-recovery: Scaling ML Inference service...")
        await self._delay(3)
        self._log("✅ ML Inference scaled to 3 instances, latency normalized")
        
        print("\n✅ Scenario Complete: Health monitoring detected and recovered incident")
        print(f"   - Incident: {incident['incident_id']}")
        print(f"   - Resolution: Auto-scaled service")
    
    async def scenario_pp_audit_query(self):
        """
        Scenario: FLOW-PP-AUDIT-001 - Subscription Audit Query
        Reference: flow_definitions.yml → FLOW-PP-AUDIT-001
        Duration: <1 second
        """
        print(f"\n{'='*80}")
        print("SCENARIO: PP Audit Query (FLOW-PP-AUDIT-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Systems Architect searches audit logs
        self._log("🔍 Systems Architect query: 'Show all approvals for agent_001'")
        await self._delay(1)
        
        # Step 2: Query PostgreSQL index
        self._log("📊 Querying PostgreSQL audit_log_index...")
        filters = {"agent_id": "agent_001", "event_type": "approval_granted"}
        results = self.db.get_audit_logs(filters)
        self._log(f"   Found {len(results)} matching events")
        await self._delay(1)
        
        # Step 3: Fetch from GCS (hash-chained logs)
        self._log("☁️  Fetching detailed logs from GCS...")
        await self._delay(1)
        
        # Step 4: Render timeline
        self._log("📅 Rendering audit timeline:")
        for i, log in enumerate(results, 1):
            self._log(f"   {i}. {log['timestamp']} - {log['event_type']}")
        
        print("\n✅ Scenario Complete: Audit query executed in 3 seconds (simulated)")
        print(f"   - Query: {filters}")
        print(f"   - Results: {len(results)} events")
    
    async def scenario_pp_support_ticket(self):
        """
        Scenario: FLOW-PP-TICKET-001 - Support Ticket Lifecycle
        Reference: flow_definitions.yml → FLOW-PP-TICKET-001
        Duration: 5-15 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: PP Support Ticket (FLOW-PP-TICKET-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Customer submits ticket
        ticket = {
            "ticket_id": "ticket_001",
            "customer_id": "cust_001",
            "subject": "Agent X failed to publish blog post",
            "description": "WordPress OAuth token expired",
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.db.create_ticket(ticket)
        self._log("📋 Ticket created: ticket_001")
        self._log(f"   Subject: {ticket['subject']}")
        await self._delay(1)
        
        # Step 2: Create GitHub Issue
        self._log("🐙 Creating GitHub Issue...")
        self._log("   Repository: dlai-sd/WAOOAW")
        self._log("   Labels: bug, high-priority")
        await self._delay(2)
        github_issue_url = "https://github.com/dlai-sd/WAOOAW/issues/42"
        self._log(f"   ✅ GitHub Issue created: {github_issue_url}")
        await self._delay(1)
        
        # Step 3: Assign to Systems Architect
        self._log("👤 Assigned to: @systems-architect-agent")
        await self._delay(1)
        
        # Step 4: Systems Architect investigates
        self._log("🔍 Systems Architect investigating...")
        await self._delay(3)
        self._log("   Root cause: OAuth token expired (no refresh)")
        await self._delay(1)
        
        # Step 5: Resolve ticket
        self._log("🔧 Fix: Trigger OAuth token refresh")
        await self._delay(2)
        self._log("✅ Ticket resolved: OAuth token refreshed")
        ticket["status"] = "resolved"
        
        print("\n✅ Scenario Complete: Ticket resolved in 10 seconds (simulated)")
        print(f"   - Ticket: {ticket['ticket_id']}")
        print(f"   - GitHub Issue: {github_issue_url}")
        print(f"   - Status: {ticket['status']}")
    
    async def scenario_pp_deployment(self):
        """
        Scenario: FLOW-PP-DEPLOY-001 - Production Deployment
        Reference: flow_definitions.yml → FLOW-PP-DEPLOY-001
        Duration: 30-60 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: PP Deployment (FLOW-PP-DEPLOY-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Trigger deployment (git push)
        self._log("🚀 Deployment triggered: git push to main branch")
        self._log("   Commit: abc123 - 'Fix OAuth token refresh'")
        await self._delay(2)
        
        # Step 2: GitHub Actions workflow
        self._log("⚙️  GitHub Actions workflow started...")
        self._log("   Job 1/5: Lint & Test")
        await self._delay(3)
        self._log("   ✅ All tests passed")
        
        self._log("   Job 2/5: Build Docker images (17 services)")
        await self._delay(5)
        self._log("   ✅ Images pushed to Artifact Registry")
        
        self._log("   Job 3/5: Deploy to Green environment")
        await self._delay(5)
        self._log("   ✅ Green environment deployed")
        
        self._log("   Job 4/5: Smoke tests")
        await self._delay(3)
        self._log("   ✅ Health checks passed")
        
        self._log("   Job 5/5: Blue-Green cutover")
        await self._delay(2)
        self._log("   ✅ Traffic routed to Green")
        
        # Step 3: Monitor for 30 minutes
        self._log("⏳ Monitoring Green environment for 30 minutes...")
        await self._delay(3)
        self._log("✅ No errors detected, deployment successful")
        
        # Step 4: Decommission Blue
        self._log("🗑️  Decommissioning Blue environment...")
        await self._delay(1)
        self._log("✅ Blue environment deleted")
        
        print("\n✅ Scenario Complete: Deployment completed in 24 seconds (simulated)")
        print("   - Strategy: Blue-Green")
        print("   - Services: 17")
        print("   - Downtime: 0 seconds")
    
    # =========================================================================
    # CROSS-JOURNEY SCENARIOS
    # =========================================================================
    
    async def scenario_config_update_propagation(self):
        """
        Scenario: FLOW-CONFIG-UPDATE-001 - Config Update Propagation
        Reference: flow_definitions.yml → FLOW-CONFIG-UPDATE-001
        Duration: <60 seconds
        """
        print(f"\n{'='*80}")
        print("SCENARIO: Config Update Propagation (FLOW-CONFIG-UPDATE-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Update config
        self._log("⚙️  Updating config: TRIAL_DURATION_DAYS = 14 (was 7)")
        await self._delay(1)
        
        # Step 2: Publish to Pub/Sub
        self._log("📢 Publishing config-update-event to Pub/Sub...")
        await self._delay(1)
        
        # Step 3: Services subscribe and update
        services = ["Customer Service", "Subscription Manager", "Plant Orchestrator"]
        self._log("📥 Services receiving update:")
        for service in services:
            self._log(f"   {service} updated config")
            await self._delay(1)
        
        # Step 4: Invalidate Redis cache
        self._log("🗑️  Invalidating Redis cache for config keys...")
        await self._delay(1)
        
        self._log("✅ Config propagated to all services in 5 seconds")
        
        print("\n✅ Scenario Complete: Config update propagated successfully")
    
    async def scenario_oauth_token_refresh(self):
        """
        Scenario: FLOW-OAUTH-REFRESH-001 - OAuth Token Refresh
        Reference: flow_definitions.yml → FLOW-OAUTH-REFRESH-001
        Duration: <5 seconds
        """
        print(f"\n{'='*80}")
        print("SCENARIO: OAuth Token Refresh (FLOW-OAUTH-REFRESH-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Agent action fails (token expired)
        self._log("❌ Agent action failed: WordPress OAuth token expired")
        await self._delay(1)
        
        # Step 2: Outside World Connector detects expiration
        self._log("🔍 Outside World Connector detected expired token")
        await self._delay(1)
        
        # Step 3: Refresh token
        self._log("🔄 Refreshing WordPress OAuth token...")
        await self._delay(2)
        self._log("✅ New token acquired (expires in 1 hour)")
        await self._delay(1)
        
        # Step 4: Store in Secret Manager
        self._log("🔐 Storing new token in GCP Secret Manager...")
        await self._delay(1)
        
        # Step 5: Retry action
        self._log("🔄 Retrying agent action...")
        await self._delay(1)
        self._log("✅ Action succeeded!")
        
        print("\n✅ Scenario Complete: OAuth token refreshed in 6 seconds")
    
    async def scenario_incident_response(self):
        """
        Scenario: FLOW-INCIDENT-RESPONSE-001 - Incident Detection & Recovery
        Reference: flow_definitions.yml → FLOW-INCIDENT-RESPONSE-001
        Duration: 5-30 minutes
        """
        print(f"\n{'='*80}")
        print("SCENARIO: Incident Response (FLOW-INCIDENT-RESPONSE-001)")
        print(f"{'='*80}\n")
        
        # Step 1: Anomaly detected
        self._log("🚨 Health Aggregator detected anomaly:")
        self._log("   Service: PostgreSQL")
        self._log("   Metric: Connection pool exhausted")
        await self._delay(2)
        
        # Step 2: Create incident
        incident = {
            "incident_id": "incident_002",
            "severity": "critical",
            "service": "PostgreSQL",
            "description": "Connection pool exhausted",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.db.create_incident(incident)
        self._log(f"📋 Critical incident created: {incident['incident_id']}")
        await self._delay(1)
        
        # Step 3: Alert Systems Architect
        self._log("🚨 CRITICAL ALERT sent to Systems Architect Agent")
        self._log("   Slack: #platform-alerts")
        self._log("   Email: architect@waooaw.com")
        await self._delay(2)
        
        # Step 4: Auto-recovery
        self._log("🔧 Auto-recovery initiated:")
        self._log("   Action 1: Increase PostgreSQL max_connections to 200")
        await self._delay(3)
        self._log("   Action 2: Scale Cloud Run services to min_instances=0")
        await self._delay(2)
        self._log("   ✅ Connection pool restored, incident resolved")
        
        print("\n✅ Scenario Complete: Incident detected and resolved in 10 seconds")
        print(f"   - Incident: {incident['incident_id']}")
        print(f"   - Resolution: Auto-recovery")
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    async def _delay(self, seconds: float):
        """Simulate delay (skip if quick mode)"""
        if self.config.enable_delays:
            await asyncio.sleep(seconds * 0.5)  # Speed up simulation by 2x
    
    def _log(self, message: str):
        """Print log message"""
        if self.config.verbose:
            print(f"[{self._elapsed()}] {message}")
    
    def _elapsed(self) -> str:
        """Get elapsed time"""
        elapsed = time.time() - self.start_time
        return f"{elapsed:6.2f}s"
    
    async def print_summary(self):
        """Print simulation summary"""
        print(f"\n{'='*80}")
        print("SIMULATION SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Duration: {self._elapsed()}")
        print(f"Mode: {self.config.mode.value}")
        print(f"\nDatabase State:")
        print(f"  - Customers: {len(self.db.customers)}")
        print(f"  - Agents: {len(self.db.agents)}")
        print(f"  - Approvals: {len(self.db.approvals)}")
        print(f"  - Audit Logs: {len(self.db.audit_logs)}")
        print(f"  - Incidents: {len(self.db.incidents)}")
        print(f"  - Tickets: {len(self.db.tickets)}")
        
        print(f"\nAgent Status:")
        for agent in self.db.agents.values():
            print(f"  - {agent.agent_id}: {agent.status.value}")
        
        print(f"\nAudit Log Events:")
        event_types = {}
        for log in self.db.audit_logs:
            event_type = log["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        for event_type, count in sorted(event_types.items()):
            print(f"  - {event_type}: {count}")
        
        print(f"\n{'='*80}")
        print("✅ SIMULATION COMPLETE")
        print(f"{'='*80}\n")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point"""
    config = SimulationConfig(
        mode=SimulationMode.FULL,
        enable_delays=True,
        enable_failures=True,
        verbose=True,
    )
    
    engine = SimulationEngine(config)
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
