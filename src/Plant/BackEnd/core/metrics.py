"""
Prometheus metrics for monitoring application health and performance.

Features:
- HTTP request metrics (counter, histogram)  
- Database connection pool metrics (gauge)
- Business metrics (agent goals, trials, customers)
- Custom metric registration
- /metrics endpoint integration

Usage:
    from core.metrics import (
        setup_metrics, 
        http_requests_total, 
        http_request_duration_seconds,
        record_http_request
    )
    
    # At app startup
    setup_metrics(app)
    
    # In middleware or handler
    record_http_request(method="GET", path="/api/v1/agents", status_code=200, duration=0.123)
"""

import time
from typing import Any, Optional
from fastapi import FastAPI, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Create registry for metrics
registry = CollectorRegistry()

# ========== APPLICATION INFO ==========
app_info = Info(
    'waooaw_plant_backend',
    'WAOOAW Plant Backend application information',
    registry=registry
)

# ========== HTTP METRICS ==========
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'path'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'path'],
    registry=registry
)

# ========== DATABASE METRICS ==========
db_connections_total = Gauge(
    'db_connections_total',
    'Total number of database connections',
    ['state'],  # active, idle, total
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],  # select, insert, update, delete
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry
)

# ========== BUSINESS METRICS ==========
active_trials_total = Gauge(
    'active_trials_total',
    'Number of active customer trials',
    registry=registry
)

agents_available_total = Gauge(
    'agents_available_total',
    'Number of agents available for hire',
    ['status'],  # available, working, offline
    registry=registry
)

goals_created_total = Counter(
    'goals_created_total',
    'Total number of goals created',
    ['agent_type'],
    registry=registry
)

goals_executed_total = Counter(
    'goals_executed_total',
    'Total number of goals executed',
    ['agent_type', 'status'],  # status: success, failure
    registry=registry
)

customer_signups_total = Counter(
    'customer_signups_total',
    'Total number of customer signups',
    registry=registry
)

# ========== APPLICATION HEALTH ==========
application_version = Gauge(
    'application_version',
    'Application version info',
    ['version'],
    registry=registry
)

uptime_seconds = Gauge(
    'uptime_seconds',
    'Application uptime in seconds',
    registry=registry
)


# ========== HELPER FUNCTIONS ==========
def record_http_request(
    method: str,
    path: str,
    status_code: int,
    duration: float
) -> None:
    """
    Record HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, path=path, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)


def record_db_query(query_type: str, duration: float) -> None:
    """
    Record database query metrics.
    
    Args:
        query_type: Type of query (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def update_db_connection_metrics(active: int, idle: int, total: int) -> None:
    """
    Update database connection pool metrics.
    
    Args:
        active: Number of active connections
        idle: Number of idle connections
        total: Total connections in pool
    """
    db_connections_total.labels(state='active').set(active)
    db_connections_total.labels(state='idle').set(idle)
    db_connections_total.labels(state='total').set(total)


def update_business_metrics(
    active_trials: Optional[int] = None,
    available_agents: Optional[int] = None,
    working_agents: Optional[int] = None,
    offline_agents: Optional[int] = None
) -> None:
    """
    Update business metrics.
    
    Args:
        active_trials: Number of active trials
        available_agents: Number of available agents
        working_agents: Number of working agents
        offline_agents: Number of offline agents
    """
    if active_trials is not None:
        active_trials_total.set(active_trials)
    if available_agents is not None:
        agents_available_total.labels(status='available').set(available_agents)
    if working_agents is not None:
        agents_available_total.labels(status='working').set(working_agents)
    if offline_agents is not None:
        agents_available_total.labels(status='offline').set(offline_agents)


# ========== METRICS ENDPOINT ==========
def setup_metrics(app: FastAPI, version: str = "0.1.0") -> None:
    """
    Setup Prometheus metrics endpoint and initialize app info.
    
    Args:
        app: FastAPI application instance
        version: Application version
    """
    # Set application info
    app_info.info({
        'version': version,
        'name': 'WAOOAW Plant Backend',
        'description': 'AI Agent Platform - Backend API'
    })
    
    # Set initial version metric
    application_version.labels(version=version).set(1)
    
    # Store startup time for uptime calculation
    startup_time = time.time()
    
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        # Update uptime
        uptime_seconds.set(time.time() - startup_time)
        
        # Generate metrics in Prometheus text format
        metrics_data = generate_latest(registry)
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Health check endpoint for load balancers."""
        return {
            "status": "healthy",
            "version": version,
            "uptime": time.time() - startup_time
        }


# ========== METRICS MIDDLEWARE ==========
class MetricsMiddleware:
    """
    Middleware to automatically collect HTTP metrics.
    
    Usage:
        from starlette.middleware.base import BaseHTTPMiddleware
        app.add_middleware(MetricsMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request and record metrics."""
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        # Extract request details
        method = scope['method']
        path = scope['path']
        
        # Skip metrics endpoint itself
        if path == '/metrics':
            await self.app(scope, receive, send)
            return
        
        # Increment in-progress gauge
        http_requests_in_progress.labels(method=method, path=path).inc()
        
        start_time = time.time()
        status_code = 500  # Default to error
        
        async def send_wrapper(message):
            """Capture response status code."""
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Record metrics
            duration = time.time() - start_time
            record_http_request(method, path, status_code, duration)
            http_requests_in_progress.labels(method=method, path=path).dec()
