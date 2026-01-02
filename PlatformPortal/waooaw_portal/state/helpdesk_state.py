"""
Help Desk State Management
Story 5.1.12: Real-time incident tracking and automated diagnostics
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class Incident:
    """Incident record"""
    incident_id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    status: str  # open, investigating, in_progress, resolved, closed
    category: str  # performance, availability, error, security, configuration
    affected_agent: str
    affected_component: str
    reported_by: str
    assigned_to: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    sla_deadline: str
    sla_status: str  # on_track, at_risk, breached
    time_to_resolve_min: Optional[int]
    tags: List[str] = field(default_factory=list)


@dataclass
class DiagnosticResult:
    """Automated diagnostic result"""
    check_name: str
    status: str  # pass, fail, warning, info
    message: str
    details: str
    timestamp: str
    recommendation: Optional[str] = None


@dataclass
class ResolutionStep:
    """Resolution workflow step"""
    step_number: int
    title: str
    description: str
    status: str  # pending, in_progress, completed, skipped
    assigned_to: Optional[str]
    duration_min: Optional[int]
    notes: Optional[str] = None


@dataclass
class KnowledgeArticle:
    """Knowledge base article"""
    article_id: str
    title: str
    summary: str
    category: str
    tags: List[str]
    views: int
    helpful_count: int
    last_updated: str


class HelpDeskState(rx.State):
    """State management for help desk and incident tracking"""
    
    # Incidents
    incidents: List[Incident] = []
    selected_incident: Optional[str] = None
    
    # Filters
    filter_severity: str = "all"  # all, critical, high, medium, low
    filter_status: str = "all"  # all, open, investigating, in_progress, resolved, closed
    filter_category: str = "all"  # all, performance, availability, error, security, configuration
    search_query: str = ""
    
    # Diagnostics
    diagnostic_results: List[DiagnosticResult] = []
    is_running_diagnostics: bool = False
    diagnostics_complete: bool = False
    
    # Resolution workflow
    resolution_steps: List[ResolutionStep] = []
    current_resolution_step: int = 0
    resolution_notes: str = ""
    
    # Knowledge base
    knowledge_articles: List[KnowledgeArticle] = []
    selected_article: Optional[str] = None
    
    # Statistics
    total_incidents: int = 0
    open_incidents: int = 0
    critical_incidents: int = 0
    avg_resolution_time_min: float = 0.0
    sla_compliance_pct: float = 0.0
    
    # New incident form
    new_incident_title: str = ""
    new_incident_description: str = ""
    new_incident_severity: str = "medium"
    new_incident_category: str = "error"
    new_incident_agent: str = ""
    
    def load_incidents(self):
        """Load incidents with mock data"""
        now = datetime.now()
        
        self.incidents = [
            Incident(
                incident_id="INC-001",
                title="High Memory Usage on Content Writer AI",
                description="Agent consuming 95% memory, causing slow response times",
                severity="critical",
                status="investigating",
                category="performance",
                affected_agent="agent-001",
                affected_component="Memory Manager",
                reported_by="system@waooaw.com",
                assigned_to="admin@waooaw.com",
                created_at=(now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=None,
                sla_deadline=(now + timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="on_track",
                time_to_resolve_min=None,
                tags=["memory", "performance", "urgent"],
            ),
            Incident(
                incident_id="INC-002",
                title="API Rate Limit Exceeded - Math Tutor",
                description="OpenAI API rate limit exceeded, requests failing",
                severity="high",
                status="in_progress",
                category="error",
                affected_agent="agent-002",
                affected_component="API Client",
                reported_by="agent-002@waooaw.com",
                assigned_to="admin@waooaw.com",
                created_at=(now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=(now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=None,
                sla_deadline=(now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="at_risk",
                time_to_resolve_min=None,
                tags=["api", "rate-limit", "external"],
            ),
            Incident(
                incident_id="INC-003",
                title="Database Connection Pool Exhausted",
                description="All database connections in use, new requests timing out",
                severity="critical",
                status="open",
                category="availability",
                affected_agent="multiple",
                affected_component="Database Connection Pool",
                reported_by="monitoring@waooaw.com",
                assigned_to=None,
                created_at=(now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=(now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=None,
                sla_deadline=(now + timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="on_track",
                time_to_resolve_min=None,
                tags=["database", "connection-pool", "critical"],
            ),
            Incident(
                incident_id="INC-004",
                title="Deployment Failed - SDR Agent v3.1.0",
                description="Agent deployment failed during health checks",
                severity="medium",
                status="resolved",
                category="configuration",
                affected_agent="agent-003",
                affected_component="Deployment Pipeline",
                reported_by="ci-cd@waooaw.com",
                assigned_to="admin@waooaw.com",
                created_at=(now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=(now - timedelta(hours=4, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=(now - timedelta(hours=4, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_deadline=(now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="on_track",
                time_to_resolve_min=30,
                tags=["deployment", "health-check", "resolved"],
            ),
            Incident(
                incident_id="INC-005",
                title="Security Alert: Unauthorized Access Attempt",
                description="Multiple failed login attempts from unusual location",
                severity="high",
                status="investigating",
                category="security",
                affected_agent="portal",
                affected_component="Authentication Service",
                reported_by="security@waooaw.com",
                assigned_to="admin@waooaw.com",
                created_at=(now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=(now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=None,
                sla_deadline=(now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="on_track",
                time_to_resolve_min=None,
                tags=["security", "authentication", "unauthorized"],
            ),
            Incident(
                incident_id="INC-006",
                title="Slow Query Performance - Agent Analytics",
                description="Analytics queries taking >10s, causing timeout errors",
                severity="medium",
                status="closed",
                category="performance",
                affected_agent="analytics",
                affected_component="Query Engine",
                reported_by="analytics@waooaw.com",
                assigned_to="admin@waooaw.com",
                created_at=(now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=(now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
                resolved_at=(now - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_deadline=(now - timedelta(hours=16)).strftime("%Y-%m-%d %H:%M:%S"),
                sla_status="on_track",
                time_to_resolve_min=360,
                tags=["performance", "database", "query"],
            ),
        ]
        
        self._update_statistics()
    
    def load_knowledge_articles(self):
        """Load knowledge base articles"""
        self.knowledge_articles = [
            KnowledgeArticle(
                article_id="KB-001",
                title="Troubleshooting High Memory Usage",
                summary="Step-by-step guide to identify and resolve memory leaks in agents",
                category="performance",
                tags=["memory", "troubleshooting", "performance"],
                views=245,
                helpful_count=89,
                last_updated="2026-01-10",
            ),
            KnowledgeArticle(
                article_id="KB-002",
                title="Handling API Rate Limits",
                summary="Best practices for managing third-party API rate limits and implementing backoff strategies",
                category="error",
                tags=["api", "rate-limit", "best-practices"],
                views=178,
                helpful_count=65,
                last_updated="2026-01-12",
            ),
            KnowledgeArticle(
                article_id="KB-003",
                title="Database Connection Pool Configuration",
                summary="Optimizing database connection pool settings for high-traffic agents",
                category="configuration",
                tags=["database", "connection-pool", "optimization"],
                views=132,
                helpful_count=48,
                last_updated="2026-01-08",
            ),
            KnowledgeArticle(
                article_id="KB-004",
                title="Deployment Health Check Failures",
                summary="Common causes of deployment health check failures and how to fix them",
                category="configuration",
                tags=["deployment", "health-check", "troubleshooting"],
                views=95,
                helpful_count=34,
                last_updated="2026-01-14",
            ),
            KnowledgeArticle(
                article_id="KB-005",
                title="Security Incident Response Playbook",
                summary="Standardized response procedures for security incidents",
                category="security",
                tags=["security", "incident-response", "playbook"],
                views=201,
                helpful_count=78,
                last_updated="2026-01-05",
            ),
        ]
    
    def _update_statistics(self):
        """Update incident statistics"""
        self.total_incidents = len(self.incidents)
        self.open_incidents = len([i for i in self.incidents if i.status in ["open", "investigating", "in_progress"]])
        self.critical_incidents = len([i for i in self.incidents if i.severity == "critical"])
        
        resolved = [i for i in self.incidents if i.time_to_resolve_min is not None]
        if resolved:
            self.avg_resolution_time_min = sum(i.time_to_resolve_min for i in resolved) / len(resolved)
        else:
            self.avg_resolution_time_min = 0.0
        
        sla_compliant = len([i for i in self.incidents if i.sla_status == "on_track"])
        self.sla_compliance_pct = (sla_compliant / self.total_incidents * 100) if self.total_incidents > 0 else 100.0
    
    def select_incident(self, incident_id: str):
        """Select incident for details view"""
        self.selected_incident = incident_id
        
        # Load diagnostic results for this incident
        incident = next((i for i in self.incidents if i.incident_id == incident_id), None)
        if incident:
            self._load_diagnostic_results(incident)
            self._load_resolution_steps(incident)
    
    def _load_diagnostic_results(self, incident: Incident):
        """Load diagnostic results for incident"""
        if incident.category == "performance":
            self.diagnostic_results = [
                DiagnosticResult(
                    check_name="Memory Usage",
                    status="fail",
                    message="Memory usage at 95% (threshold: 80%)",
                    details="Current: 15.2 GB / 16 GB allocated. Peak: 15.8 GB in last hour.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Increase memory allocation or optimize memory usage. Check for memory leaks.",
                ),
                DiagnosticResult(
                    check_name="CPU Usage",
                    status="warning",
                    message="CPU usage at 78% (threshold: 75%)",
                    details="Current: 6.2 cores / 8 cores. Average: 65% over last 15 min.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Monitor for sustained high CPU. Consider scaling horizontally.",
                ),
                DiagnosticResult(
                    check_name="Disk I/O",
                    status="pass",
                    message="Disk I/O within normal limits",
                    details="Read: 45 MB/s, Write: 28 MB/s. Latency: 8ms average.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                ),
                DiagnosticResult(
                    check_name="Network",
                    status="pass",
                    message="Network throughput normal",
                    details="Inbound: 125 Mbps, Outbound: 89 Mbps. Latency: 12ms.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                ),
            ]
        elif incident.category == "error":
            self.diagnostic_results = [
                DiagnosticResult(
                    check_name="API Connectivity",
                    status="fail",
                    message="OpenAI API rate limit exceeded",
                    details="429 errors: 45 in last 5 minutes. Rate: 3500 req/min (limit: 3000).",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Implement exponential backoff. Consider upgrading API tier.",
                ),
                DiagnosticResult(
                    check_name="Request Queue",
                    status="warning",
                    message="Request queue building up",
                    details="Queue depth: 1,234 requests. Processing rate: 45 req/sec.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Drain queue or increase processing capacity.",
                ),
                DiagnosticResult(
                    check_name="Error Rate",
                    status="fail",
                    message="Error rate above threshold",
                    details="Error rate: 12.5% (threshold: 5%). Total errors: 567 in last hour.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Review error logs and implement retry logic.",
                ),
            ]
        elif incident.category == "availability":
            self.diagnostic_results = [
                DiagnosticResult(
                    check_name="Database Connections",
                    status="fail",
                    message="Connection pool exhausted",
                    details="Active: 100/100, Idle: 0, Waiting: 45 requests.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Increase pool size or identify slow queries holding connections.",
                ),
                DiagnosticResult(
                    check_name="Connection Leaks",
                    status="warning",
                    message="Possible connection leaks detected",
                    details="15 connections held for >5 minutes. Average hold time: 8.3 minutes.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    recommendation="Review code for unclosed database connections.",
                ),
                DiagnosticResult(
                    check_name="Query Performance",
                    status="pass",
                    message="Query performance acceptable",
                    details="Average query time: 45ms. P95: 120ms. P99: 250ms.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                ),
            ]
        else:
            self.diagnostic_results = [
                DiagnosticResult(
                    check_name="System Health",
                    status="info",
                    message="Running diagnostic checks...",
                    details="No specific diagnostic results available for this incident type.",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                ),
            ]
    
    def _load_resolution_steps(self, incident: Incident):
        """Load resolution workflow steps"""
        if incident.status == "open":
            self.resolution_steps = [
                ResolutionStep(1, "Acknowledge Incident", "Assign incident to team member", "pending", None, None),
                ResolutionStep(2, "Run Diagnostics", "Execute automated diagnostic checks", "pending", None, None),
                ResolutionStep(3, "Identify Root Cause", "Analyze diagnostic results", "pending", None, None),
                ResolutionStep(4, "Implement Fix", "Apply resolution based on root cause", "pending", None, None),
                ResolutionStep(5, "Verify Resolution", "Confirm incident is resolved", "pending", None, None),
                ResolutionStep(6, "Close Incident", "Document resolution and close ticket", "pending", None, None),
            ]
            self.current_resolution_step = 0
        elif incident.status == "investigating":
            self.resolution_steps = [
                ResolutionStep(1, "Acknowledge Incident", "Assign incident to team member", "completed", "admin@waooaw.com", 2),
                ResolutionStep(2, "Run Diagnostics", "Execute automated diagnostic checks", "in_progress", "admin@waooaw.com", None),
                ResolutionStep(3, "Identify Root Cause", "Analyze diagnostic results", "pending", None, None),
                ResolutionStep(4, "Implement Fix", "Apply resolution based on root cause", "pending", None, None),
                ResolutionStep(5, "Verify Resolution", "Confirm incident is resolved", "pending", None, None),
                ResolutionStep(6, "Close Incident", "Document resolution and close ticket", "pending", None, None),
            ]
            self.current_resolution_step = 1
        elif incident.status == "in_progress":
            self.resolution_steps = [
                ResolutionStep(1, "Acknowledge Incident", "Assign incident to team member", "completed", "admin@waooaw.com", 1),
                ResolutionStep(2, "Run Diagnostics", "Execute automated diagnostic checks", "completed", "admin@waooaw.com", 3),
                ResolutionStep(3, "Identify Root Cause", "Analyze diagnostic results", "completed", "admin@waooaw.com", 15),
                ResolutionStep(4, "Implement Fix", "Apply resolution based on root cause", "in_progress", "admin@waooaw.com", None),
                ResolutionStep(5, "Verify Resolution", "Confirm incident is resolved", "pending", None, None),
                ResolutionStep(6, "Close Incident", "Document resolution and close ticket", "pending", None, None),
            ]
            self.current_resolution_step = 3
        else:  # resolved or closed
            self.resolution_steps = [
                ResolutionStep(1, "Acknowledge Incident", "Assign incident to team member", "completed", "admin@waooaw.com", 1),
                ResolutionStep(2, "Run Diagnostics", "Execute automated diagnostic checks", "completed", "admin@waooaw.com", 2),
                ResolutionStep(3, "Identify Root Cause", "Analyze diagnostic results", "completed", "admin@waooaw.com", 10),
                ResolutionStep(4, "Implement Fix", "Apply resolution based on root cause", "completed", "admin@waooaw.com", 15),
                ResolutionStep(5, "Verify Resolution", "Confirm incident is resolved", "completed", "admin@waooaw.com", 2),
                ResolutionStep(6, "Close Incident", "Document resolution and close ticket", "completed", "admin@waooaw.com", 1),
            ]
            self.current_resolution_step = 6
    
    async def run_diagnostics(self, incident_id: str):
        """Run automated diagnostics for incident"""
        self.is_running_diagnostics = True
        self.diagnostics_complete = False
        yield
        
        # Simulate diagnostic execution
        import asyncio
        await asyncio.sleep(3)
        
        self.is_running_diagnostics = False
        self.diagnostics_complete = True
        
        # Update incident status
        incident = next((i for i in self.incidents if i.incident_id == incident_id), None)
        if incident and incident.status == "open":
            incident.status = "investigating"
            incident.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._update_statistics()
    
    def update_incident_status(self, incident_id: str, new_status: str):
        """Update incident status"""
        incident = next((i for i in self.incidents if i.incident_id == incident_id), None)
        if incident:
            incident.status = new_status
            incident.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if new_status in ["resolved", "closed"]:
                incident.resolved_at = incident.updated_at
                # Calculate resolution time
                created = datetime.strptime(incident.created_at, "%Y-%m-%d %H:%M:%S")
                resolved = datetime.strptime(incident.resolved_at, "%Y-%m-%d %H:%M:%S")
                incident.time_to_resolve_min = int((resolved - created).total_seconds() / 60)
            
            self._update_statistics()
            
            # Reload resolution steps
            if incident_id == self.selected_incident:
                self._load_resolution_steps(incident)
    
    def assign_incident(self, incident_id: str, assignee: str):
        """Assign incident to team member"""
        incident = next((i for i in self.incidents if i.incident_id == incident_id), None)
        if incident:
            incident.assigned_to = assignee
            incident.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if incident.status == "open":
                incident.status = "investigating"
    
    def create_incident(self):
        """Create new incident"""
        now = datetime.now()
        
        # Determine SLA deadline based on severity
        sla_hours = {"critical": 1, "high": 4, "medium": 8, "low": 24}
        deadline = now + timedelta(hours=sla_hours.get(self.new_incident_severity, 8))
        
        new_incident = Incident(
            incident_id=f"INC-{len(self.incidents) + 1:03d}",
            title=self.new_incident_title,
            description=self.new_incident_description,
            severity=self.new_incident_severity,
            status="open",
            category=self.new_incident_category,
            affected_agent=self.new_incident_agent,
            affected_component="Unknown",
            reported_by="manual@waooaw.com",
            assigned_to=None,
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            resolved_at=None,
            sla_deadline=deadline.strftime("%Y-%m-%d %H:%M:%S"),
            sla_status="on_track",
            time_to_resolve_min=None,
            tags=[],
        )
        
        self.incidents.insert(0, new_incident)
        self._update_statistics()
        
        # Clear form
        self.new_incident_title = ""
        self.new_incident_description = ""
        self.new_incident_severity = "medium"
        self.new_incident_category = "error"
        self.new_incident_agent = ""
    
    @rx.var
    def filtered_incidents(self) -> List[Incident]:
        """Filter incidents based on current filters"""
        filtered = self.incidents
        
        if self.filter_severity != "all":
            filtered = [i for i in filtered if i.severity == self.filter_severity]
        
        if self.filter_status != "all":
            filtered = [i for i in filtered if i.status == self.filter_status]
        
        if self.filter_category != "all":
            filtered = [i for i in filtered if i.category == self.filter_category]
        
        if self.search_query:
            query = self.search_query.lower()
            filtered = [i for i in filtered if query in i.title.lower() or query in i.description.lower()]
        
        return filtered
    
    @rx.var
    def selected_incident_details(self) -> Optional[Incident]:
        """Get selected incident details"""
        if self.selected_incident:
            return next((i for i in self.incidents if i.incident_id == self.selected_incident), None)
        return None
    
    @rx.var
    def has_diagnostics(self) -> bool:
        """Check if diagnostic results exist"""
        return len(self.diagnostic_results) > 0
    
    @rx.var
    def has_resolution_steps(self) -> bool:
        """Check if resolution steps exist"""
        return len(self.resolution_steps) > 0
    
    @rx.var
    def filtered_incidents_count(self) -> int:
        """Count of filtered incidents"""
        return len(self.filtered_incidents)
