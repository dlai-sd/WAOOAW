"""
Audit Logging Middleware - GW-104

Async audit log writer for all gateway requests.
Captures request/response, OPA decisions, latency, correlation IDs.

Writes to PostgreSQL gateway_audit_logs table in batches every 5 seconds.
"""

import asyncio
import asyncpg
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

logger = logging.getLogger(__name__)

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit Logging Middleware for CP and PP Gateways.
    
    Constitutional Requirement (GW-001):
    - Log ALL gateway requests (100% coverage)
    - Capture: request, response, OPA decisions, latency, errors
    - Correlation ID: Trace requests across services
    - Causation ID: Link parent requests
    
    Performance:
    - Async writes (non-blocking)
    - Batch inserts every 5 seconds (reduces DB load)
    - Average overhead: <2ms per request
    
    PostgreSQL Schema:
    - Table: gateway_audit_logs (19 columns)
    - Indexes: correlation_id, user_id, timestamp, errors, OPA decisions
    - RLS: Row-level security (users see own logs)
    - Partitioning: Monthly partitions (90-day retention)
    
    Configuration:
    - DATABASE_URL: PostgreSQL connection string
    - GATEWAY_TYPE: "CP" or "PP"
    - BATCH_INTERVAL: Seconds between batch inserts (default: 5)
    - BATCH_SIZE: Max logs per batch (default: 100)
    """
    
    def __init__(
        self,
        app,
        database_url: str,
        gateway_type: str,
        batch_interval: int = 5,
        batch_size: int = 100
    ):
        super().__init__(app)
        self.database_url = database_url
        self.gateway_type = gateway_type.upper()
        self.batch_interval = batch_interval
        self.batch_size = batch_size
        
        # In-memory buffer for audit logs (before batch insert)
        self.audit_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = asyncio.Lock()
        
        # Database connection pool
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Background task for batch inserts
        self.batch_task: Optional[asyncio.Task] = None
    
    async def _init_db_pool(self):
        """Initialize PostgreSQL connection pool."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=5
            )
            logger.info("Audit logging database pool initialized")
    
    async def _start_batch_writer(self):
        """Start background task for batch inserts."""
        if not self.batch_task or self.batch_task.done():
            self.batch_task = asyncio.create_task(self._batch_writer_loop())
            logger.info("Audit logging batch writer started")
    
    async def _batch_writer_loop(self):
        """Background task that writes audit logs every N seconds."""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_audit_buffer()
            except asyncio.CancelledError:
                # Final flush before shutdown
                await self._flush_audit_buffer()
                break
            except Exception as e:
                logger.error(f"Batch writer error: {e}", exc_info=True)
    
    async def _flush_audit_buffer(self):
        """Flush audit buffer to PostgreSQL in batches."""
        async with self.buffer_lock:
            if not self.audit_buffer:
                return
            
            # Take up to batch_size logs
            logs_to_insert = self.audit_buffer[:self.batch_size]
            self.audit_buffer = self.audit_buffer[self.batch_size:]
        
        try:
            await self._init_db_pool()
            
            # Batch insert using COPY (fastest for bulk inserts)
            async with self.db_pool.acquire() as conn:
                # Prepare records for COPY
                records = [
                    (
                        log["id"],
                        log["correlation_id"],
                        log["causation_id"],
                        log["timestamp"],
                        log["gateway_type"],
                        log["request_id"],
                        log["http_method"],
                        log["endpoint"],
                        json.dumps(log["query_params"]) if log["query_params"] else None,
                        json.dumps(log["request_headers"]) if log["request_headers"] else None,
                        json.dumps(log["request_body"]) if log["request_body"] else None,
                        log["user_id"],
                        log["customer_id"],
                        log["email"],
                        log["roles"],
                        log["trial_mode"],
                        log["opa_policies_evaluated"],
                        json.dumps(log["opa_decisions"]) if log["opa_decisions"] else None,
                        log["opa_latency_ms"],
                        log["status_code"],
                        json.dumps(log["response_headers"]) if log["response_headers"] else None,
                        json.dumps(log["response_body"]) if log["response_body"] else None,
                        log["error_type"],
                        log["trial_mode"],  # Include trial mode in logs
                        log["error_message"],
                        log["total_latency_ms"],
                        log["plant_latency_ms"],
                        log["action"],
                        log["resource"],
                        log["resource_id"],
                        log["trial_expires_at"]  # Include trial expiration in logs
                    )
                    for log in logs_to_insert
                ]
                
                # COPY to PostgreSQL
                await conn.copy_records_to_table(
                    "gateway_audit_logs",
                    records=records,
                    columns=[
                        "id", "correlation_id", "causation_id", "timestamp",
                        "gateway_type", "request_id", "http_method", "endpoint",
                        "query_params", "request_headers", "request_body",
                        "user_id", "customer_id", "email", "roles", "trial_mode",
                        "opa_policies_evaluated", "opa_decisions", "opa_latency_ms",
                        "status_code", "response_headers", "response_body",
                        "error_type", "error_message", "total_latency_ms",
                        "plant_latency_ms", "action", "resource", "resource_id"
                    ]
                )
                
                logger.info(f"Flushed {len(logs_to_insert)} audit logs to PostgreSQL")
        
        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}", exc_info=True)
            # Put logs back in buffer for retry
            async with self.buffer_lock:
                self.audit_buffer = logs_to_insert + self.audit_buffer
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request, capture audit data, write to buffer.
        """
        # Start batch writer if not running
        await self._start_batch_writer()
        
        # Generate correlation_id (trace across services)
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Extract causation_id (parent request)
        causation_id = request.headers.get("X-Request-ID")
        
        # Record start time
        start_time = datetime.now(timezone.utc)
        
        # Extract JWT claims (if present)
        jwt_claims = getattr(request.state, "jwt", None)
        user_id = jwt_claims.get("user_id") if jwt_claims else None
        customer_id = jwt_claims.get("customer_id") if jwt_claims else None
        email = jwt_claims.get("email") if jwt_claims else None
        roles = jwt_claims.get("roles", []) if jwt_claims else []
        trial_mode = jwt_claims.get("trial_mode", False) if jwt_claims else False
        
        # Extract resource and action
        resource, action = self._extract_resource_action(request)
        resource_id = self._extract_resource_id(request)
        
        # Capture request data
        request_data = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "body": await self._get_request_body(request)
        }
        
        # Initialize OPA tracking
        opa_policies_evaluated = []
        opa_decisions = {}
        opa_latency_ms = None
        
        # Call next middleware
        try:
            response = await call_next(request)
            
            # Calculate latency
            end_time = datetime.now(timezone.utc)
            total_latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # Extract OPA data from request state (if set by policy middleware)
            if hasattr(request.state, "opa_policies_evaluated"):
                opa_policies_evaluated = request.state.opa_policies_evaluated
            if hasattr(request.state, "opa_decisions"):
                opa_decisions = request.state.opa_decisions
            if hasattr(request.state, "opa_latency_ms"):
                opa_latency_ms = request.state.opa_latency_ms
            
            # Extract Plant latency (if proxied to Plant)
            plant_latency_ms = None
            if hasattr(request.state, "plant_latency_ms"):
                plant_latency_ms = request.state.plant_latency_ms
            
            # Capture response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": None  # Don't log response body (too large, PII concerns)
            }
            
            # Build audit log
            audit_log = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "timestamp": start_time,
                "gateway_type": self.gateway_type,
                "request_id": str(uuid.uuid4()),
                "http_method": request_data["method"],
                "endpoint": request_data["endpoint"],
                "query_params": request_data["query_params"],
                "request_headers": self._sanitize_headers(request_data["headers"]),
                "request_body": request_data["body"],
                "user_id": user_id,
                "customer_id": customer_id,
                "email": email,
                "roles": roles,
                "trial_mode": trial_mode,
                "opa_policies_evaluated": opa_policies_evaluated,
                "opa_decisions": opa_decisions,
                "opa_latency_ms": opa_latency_ms,
                "status_code": response_data["status_code"],
                "response_headers": self._sanitize_headers(response_data["headers"]),
                "response_body": response_data["body"],
                "error_type": None,
                "error_message": None,
                "total_latency_ms": total_latency_ms,
                "plant_latency_ms": plant_latency_ms,
                "action": action,
                "resource": resource,
                "resource_id": resource_id
            }
            
            # Add to buffer (async, non-blocking)
            await self._add_to_buffer(audit_log)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
        
        except Exception as e:
            # Log error
            end_time = datetime.now(timezone.utc)
            total_latency_ms = (end_time - start_time).total_seconds() * 1000
            
            audit_log = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "timestamp": start_time,
                "gateway_type": self.gateway_type,
                "request_id": str(uuid.uuid4()),
                "http_method": request_data["method"],
                "endpoint": request_data["endpoint"],
                "query_params": request_data["query_params"],
                "request_headers": self._sanitize_headers(request_data["headers"]),
                "request_body": request_data["body"],
                "user_id": user_id,
                "customer_id": customer_id,
                "email": email,
                "roles": roles,
                "trial_mode": trial_mode,
                "opa_policies_evaluated": opa_policies_evaluated,
                "opa_decisions": opa_decisions,
                "opa_latency_ms": opa_latency_ms,
                "status_code": 500,
                "response_headers": {},
                "response_body": None,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "total_latency_ms": total_latency_ms,
                "plant_latency_ms": None,
                "action": action,
                "resource": resource,
                "resource_id": resource_id
            }
            
            await self._add_to_buffer(audit_log)
            
            # Re-raise exception
            raise
    
    async def _add_to_buffer(self, audit_log: Dict[str, Any]):
        """Add audit log to in-memory buffer (non-blocking)."""
        async with self.buffer_lock:
            self.audit_buffer.append(audit_log)
        
        # If buffer is too large, flush immediately
        if len(self.audit_buffer) >= self.batch_size:
            asyncio.create_task(self._flush_audit_buffer())
    
    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request body (if JSON)."""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    return json.loads(body.decode("utf-8"))
        except Exception as e:
            logger.debug(f"Failed to parse request body: {e}")
        return None
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers (Authorization, API keys, etc.)."""
        sensitive_keys = ["authorization", "api-key", "x-api-key", "cookie", "set-cookie"]
        return {
            k: "***REDACTED***" if k.lower() in sensitive_keys else v
            for k, v in headers.items()
        }
    
    def _extract_resource_action(self, request: Request) -> tuple[str, str]:
        """Extract resource and action from request."""
        path = request.url.path
        method = request.method.upper()
        
        if path.startswith("/api/v1/"):
            path = path[8:]
        
        parts = path.strip("/").split("/")
        resource = parts[0] if parts and parts[0] else "unknown"
        
        action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        
        action = action_map.get(method, "unknown")
        
        return resource, action
    
    def _extract_resource_id(self, request: Request) -> Optional[str]:
        """Extract resource ID from path (e.g., /agents/123 → 123)."""
        path = request.url.path
        if path.startswith("/api/v1/"):
            path = path[8:]
        
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            # Second part is often the resource ID
            return parts[1]
        
        return None
    
    async def close(self):
        """Close database pool and stop batch writer."""
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_audit_buffer()
        
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Audit logging database pool closed")
"""
Audit Logging Middleware - GW-104

Async audit log writer for all gateway requests.
Captures request/response, OPA decisions, latency, correlation IDs.

Writes to PostgreSQL gateway_audit_logs table in batches every 5 seconds.
"""

import asyncio
import asyncpg
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

logger = logging.getLogger(__name__)

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit Logging Middleware for CP and PP Gateways.
    
    Constitutional Requirement (GW-001):
    - Log ALL gateway requests (100% coverage)
    - Capture: request, response, OPA decisions, latency, errors
    - Correlation ID: Trace requests across services
    - Causation ID: Link parent requests
    
    Performance:
    - Async writes (non-blocking)
    - Batch inserts every 5 seconds (reduces DB load)
    - Average overhead: <2ms per request
    
    PostgreSQL Schema:
    - Table: gateway_audit_logs (19 columns)
    - Indexes: correlation_id, user_id, timestamp, errors, OPA decisions
    - RLS: Row-level security (users see own logs)
    - Partitioning: Monthly partitions (90-day retention)
    
    Configuration:
    - DATABASE_URL: PostgreSQL connection string
    - GATEWAY_TYPE: "CP" or "PP"
    - BATCH_INTERVAL: Seconds between batch inserts (default: 5)
    - BATCH_SIZE: Max logs per batch (default: 100)
    """
    
    def __init__(
        self,
        app,
        database_url: str,
        gateway_type: str,
        batch_interval: int = 5,
        batch_size: int = 100
    ):
        super().__init__(app)
        self.database_url = database_url
        self.gateway_type = gateway_type.upper()
        self.batch_interval = batch_interval
        self.batch_size = batch_size
        
        # In-memory buffer for audit logs (before batch insert)
        self.audit_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = asyncio.Lock()
        
        # Database connection pool
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Background task for batch inserts
        self.batch_task: Optional[asyncio.Task] = None
    
    async def _init_db_pool(self):
        """Initialize PostgreSQL connection pool."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=5
            )
            logger.info("Audit logging database pool initialized")
    
    async def _start_batch_writer(self):
        """Start background task for batch inserts."""
        if not self.batch_task or self.batch_task.done():
            self.batch_task = asyncio.create_task(self._batch_writer_loop())
            logger.info("Audit logging batch writer started")
    
    async def _batch_writer_loop(self):
        """Background task that writes audit logs every N seconds."""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_audit_buffer()
            except asyncio.CancelledError:
                # Final flush before shutdown
                await self._flush_audit_buffer()
                break
            except Exception as e:
                logger.error(f"Batch writer error: {e}", exc_info=True)
    
    async def _flush_audit_buffer(self):
        """Flush audit buffer to PostgreSQL in batches."""
        async with self.buffer_lock:
            if not self.audit_buffer:
                return
            
            # Take up to batch_size logs
            logs_to_insert = self.audit_buffer[:self.batch_size]
            self.audit_buffer = self.audit_buffer[self.batch_size:]
        
        try:
            await self._init_db_pool()
            
            # Batch insert using COPY (fastest for bulk inserts)
            async with self.db_pool.acquire() as conn:
                # Prepare records for COPY
                records = [
                    (
                        log["id"],
                        log["correlation_id"],
                        log["causation_id"],
                        log["timestamp"],
                        log["gateway_type"],
                        log["request_id"],
                        log["http_method"],
                        log["endpoint"],
                        json.dumps(log["query_params"]) if log["query_params"] else None,
                        json.dumps(log["request_headers"]) if log["request_headers"] else None,
                        json.dumps(log["request_body"]) if log["request_body"] else None,
                        log["user_id"],
                        log["customer_id"],
                        log["email"],
                        log["roles"],
                        log["trial_mode"],
                        log["opa_policies_evaluated"],
                        json.dumps(log["opa_decisions"]) if log["opa_decisions"] else None,
                        log["opa_latency_ms"],
                        log["status_code"],
                        json.dumps(log["response_headers"]) if log["response_headers"] else None,
                        json.dumps(log["response_body"]) if log["response_body"] else None,
                        log["error_type"],
                        log["trial_mode"],  # Include trial mode in logs
                        log["error_message"],
                        log["total_latency_ms"],
                        log["plant_latency_ms"],
                        log["action"],
                        log["resource"],
                        log["resource_id"],
                        log["trial_expires_at"]  # Include trial expiration in logs
                    )
                    for log in logs_to_insert
                ]
                
                # COPY to PostgreSQL
                await conn.copy_records_to_table(
                    "gateway_audit_logs",
                    records=records,
                    columns=[
                        "id", "correlation_id", "causation_id", "timestamp",
                        "gateway_type", "request_id", "http_method", "endpoint",
                        "query_params", "request_headers", "request_body",
                        "user_id", "customer_id", "email", "roles", "trial_mode",
                        "opa_policies_evaluated", "opa_decisions", "opa_latency_ms",
                        "status_code", "response_headers", "response_body",
                        "error_type", "error_message", "total_latency_ms",
                        "plant_latency_ms", "action", "resource", "resource_id"
                    ]
                )
                
                logger.info(f"Flushed {len(logs_to_insert)} audit logs to PostgreSQL")
        
        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}", exc_info=True)
            # Put logs back in buffer for retry
            async with self.buffer_lock:
                self.audit_buffer = logs_to_insert + self.audit_buffer
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request, capture audit data, write to buffer.
        """
        # Start batch writer if not running
        await self._start_batch_writer()
        
        # Generate correlation_id (trace across services)
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Extract causation_id (parent request)
        causation_id = request.headers.get("X-Request-ID")
        
        # Record start time
        start_time = datetime.now(timezone.utc)
        
        # Extract JWT claims (if present)
        jwt_claims = getattr(request.state, "jwt", None)
        user_id = jwt_claims.get("user_id") if jwt_claims else None
        customer_id = jwt_claims.get("customer_id") if jwt_claims else None
        email = jwt_claims.get("email") if jwt_claims else None
        roles = jwt_claims.get("roles", []) if jwt_claims else []
        trial_mode = jwt_claims.get("trial_mode", False) if jwt_claims else False
        
        # Extract resource and action
        resource, action = self._extract_resource_action(request)
        resource_id = self._extract_resource_id(request)
        
        # Capture request data
        request_data = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "body": await self._get_request_body(request)
        }
        
        # Initialize OPA tracking
        opa_policies_evaluated = []
        opa_decisions = {}
        opa_latency_ms = None
        
        # Call next middleware
        try:
            response = await call_next(request)
            
            # Calculate latency
            end_time = datetime.now(timezone.utc)
            total_latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # Extract OPA data from request state (if set by policy middleware)
            if hasattr(request.state, "opa_policies_evaluated"):
                opa_policies_evaluated = request.state.opa_policies_evaluated
            if hasattr(request.state, "opa_decisions"):
                opa_decisions = request.state.opa_decisions
            if hasattr(request.state, "opa_latency_ms"):
                opa_latency_ms = request.state.opa_latency_ms
            
            # Extract Plant latency (if proxied to Plant)
            plant_latency_ms = None
            if hasattr(request.state, "plant_latency_ms"):
                plant_latency_ms = request.state.plant_latency_ms
            
            # Capture response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": None  # Don't log response body (too large, PII concerns)
            }
            
            # Build audit log
            audit_log = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "timestamp": start_time,
                "gateway_type": self.gateway_type,
                "request_id": str(uuid.uuid4()),
                "http_method": request_data["method"],
                "endpoint": request_data["endpoint"],
                "query_params": request_data["query_params"],
                "request_headers": self._sanitize_headers(request_data["headers"]),
                "request_body": request_data["body"],
                "user_id": user_id,
                "customer_id": customer_id,
                "email": email,
                "roles": roles,
                "trial_mode": trial_mode,
                "opa_policies_evaluated": opa_policies_evaluated,
                "opa_decisions": opa_decisions,
                "opa_latency_ms": opa_latency_ms,
                "status_code": response_data["status_code"],
                "response_headers": self._sanitize_headers(response_data["headers"]),
                "response_body": response_data["body"],
                "error_type": None,
                "error_message": None,
                "total_latency_ms": total_latency_ms,
                "plant_latency_ms": plant_latency_ms,
                "action": action,
                "resource": resource,
                "resource_id": resource_id
            }
            
            # Add to buffer (async, non-blocking)
            await self._add_to_buffer(audit_log)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
        
        except Exception as e:
            # Log error
            end_time = datetime.now(timezone.utc)
            total_latency_ms = (end_time - start_time).total_seconds() * 1000
            
            audit_log = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "timestamp": start_time,
                "gateway_type": self.gateway_type,
                "request_id": str(uuid.uuid4()),
                "http_method": request_data["method"],
                "endpoint": request_data["endpoint"],
                "query_params": request_data["query_params"],
                "request_headers": self._sanitize_headers(request_data["headers"]),
                "request_body": request_data["body"],
                "user_id": user_id,
                "customer_id": customer_id,
                "email": email,
                "roles": roles,
                "trial_mode": trial_mode,
                "opa_policies_evaluated": opa_policies_evaluated,
                "opa_decisions": opa_decisions,
                "opa_latency_ms": opa_latency_ms,
                "status_code": 500,
                "response_headers": {},
                "response_body": None,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "total_latency_ms": total_latency_ms,
                "plant_latency_ms": None,
                "action": action,
                "resource": resource,
                "resource_id": resource_id
            }
            
            await self._add_to_buffer(audit_log)
            
            # Re-raise exception
            raise
    
    async def _add_to_buffer(self, audit_log: Dict[str, Any]):
        """Add audit log to in-memory buffer (non-blocking)."""
        async with self.buffer_lock:
            self.audit_buffer.append(audit_log)
        
        # If buffer is too large, flush immediately
        if len(self.audit_buffer) >= self.batch_size:
            asyncio.create_task(self._flush_audit_buffer())
    
    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request body (if JSON)."""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    return json.loads(body.decode("utf-8"))
        except Exception as e:
            logger.debug(f"Failed to parse request body: {e}")
        return None
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers (Authorization, API keys, etc.)."""
        sensitive_keys = ["authorization", "api-key", "x-api-key", "cookie", "set-cookie"]
        return {
            k: "***REDACTED***" if k.lower() in sensitive_keys else v
            for k, v in headers.items()
        }
    
    def _extract_resource_action(self, request: Request) -> tuple[str, str]:
        """Extract resource and action from request."""
        path = request.url.path
        method = request.method.upper()
        
        if path.startswith("/api/v1/"):
            path = path[8:]
        
        parts = path.strip("/").split("/")
        resource = parts[0] if parts and parts[0] else "unknown"
        
        action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        
        action = action_map.get(method, "unknown")
        
        return resource, action
    
    def _extract_resource_id(self, request: Request) -> Optional[str]:
        """Extract resource ID from path (e.g., /agents/123 → 123)."""
        path = request.url.path
        if path.startswith("/api/v1/"):
            path = path[8:]
        
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            # Second part is often the resource ID
            return parts[1]
        
        return None
    
    async def close(self):
        """Close database pool and stop batch writer."""
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_audit_buffer()
        
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Audit logging database pool closed")
