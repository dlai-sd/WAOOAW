"""Platform posting usage events and metrics.

Tracks all social platform posting attempts for:
- Analytics and reporting
- Billing and cost attribution
- Troubleshooting and debugging
- Performance monitoring
- SLA tracking
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import httpx


logger = logging.getLogger(__name__)


class PostingStatus(Enum):
    """Status of platform posting attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class PlatformPostEvent:
    """Event data for platform posting attempt."""
    
    # Identifiers
    event_type: str = "platform_post"
    correlation_id: str = ""
    customer_id: str = ""
    agent_id: str = ""
    
    # Platform details
    platform: str = ""  # youtube, instagram, facebook, linkedin, whatsapp
    credential_ref: str = ""
    
    # Status and timing
    status: str = "unknown"  # success, failed, retrying
    timestamp: str = ""  # ISO 8601 format
    duration_ms: int = 0
    
    # Success details
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    
    # Failure details  
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_transient: Optional[bool] = None
    retry_count: int = 0
    max_retries: int = 0
    
    # Additional context
    content_type: Optional[str] = None  # text, image, video, template
    content_length: Optional[int] = None  # Character/byte count
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


class PlatformMetricsCollector:
    """Collects and publishes platform posting metrics."""
    
    def __init__(
        self,
        *,
        plant_backend_url: Optional[str] = None,
        enable_remote_logging: bool = True,
    ):
        """Initialize metrics collector.
        
        Args:
            plant_backend_url: Plant Backend URL for usage events API
            enable_remote_logging: Whether to send events to backend
        """
        self._plant_backend_url = plant_backend_url or "http://localhost:8000"
        self._enable_remote_logging = enable_remote_logging
        
        # In-memory metrics (for Prometheus export in future)
        self._post_count = {}  # platform -> count
        self._success_count = {}  # platform -> count
        self._failure_count = {}  # platform -> count
        self._total_duration_ms = {}  # platform -> total duration
    
    async def log_post_attempt(
        self,
        *,
        customer_id: str,
        agent_id: str,
        platform: str,
        status: PostingStatus,
        duration_ms: int,
        credential_ref: str = "",
        post_id: Optional[str] = None,
        post_url: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        is_transient: Optional[bool] = None,
        retry_count: int = 0,
        max_retries: int = 0,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
        correlation_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log platform posting attempt as usage event.
        
        Args:
            customer_id: Customer ID (e.g., "CUST-123")
            agent_id: Agent instance ID (e.g., "AGENT-456")
            platform: Platform name (youtube, instagram, etc.)
            status: Posting status (success, failed, retrying)
            duration_ms: Request duration in milliseconds
            credential_ref: Credential reference used
            post_id: Platform-specific post ID (success only)
            post_url: Public URL to post (success only)
            error_code: Error code (failure only)
            error_message: Error message (failure only)
            is_transient: Whether error is transient (failure only)
            retry_count: Current retry attempt number
            max_retries: Maximum retry attempts configured
            content_type: Type of content (text, image, video)
            content_length: Content size in characters/bytes
            correlation_id: Correlation ID for tracing
            metadata: Additional metadata
        """
        event = PlatformPostEvent(
            correlation_id=correlation_id,
            customer_id=customer_id,
            agent_id=agent_id,
            platform=platform,
            credential_ref=credential_ref,
            status=status.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            duration_ms=duration_ms,
            post_id=post_id,
            post_url=post_url,
            error_code=error_code,
            error_message=error_message,
            is_transient=is_transient,
            retry_count=retry_count,
            max_retries=max_retries,
            content_type=content_type,
            content_length=content_length,
            metadata=metadata or {},
        )
        
        # Log to application logs
        self._log_to_app_logs(event)
        
        # Update in-memory metrics
        self._update_metrics(event)
        
        # Send to backend (async, non-blocking)
        if self._enable_remote_logging:
            try:
                await self._send_to_backend(event)
            except Exception as e:
                logger.warning(f"Failed to send usage event to backend: {e}")
    
    def _log_to_app_logs(self, event: PlatformPostEvent) -> None:
        """Log event to application logs."""
        log_msg = (
            f"[{event.correlation_id}] Platform post: "
            f"platform={event.platform} status={event.status} "
            f"duration={event.duration_ms}ms"
        )
        
        if event.status == "success":
            log_msg += f" post_id={event.post_id}"
            logger.info(log_msg)
        elif event.status == "failed":
            log_msg += f" error={event.error_code}"
            if event.retry_count > 0:
                log_msg += f" retry={event.retry_count}/{event.max_retries}"
            logger.error(log_msg)
        elif event.status == "retrying":
            log_msg += f" retry={event.retry_count}/{event.max_retries}"
            logger.warning(log_msg)
    
    def _update_metrics(self, event: PlatformPostEvent) -> None:
        """Update in-memory metrics counters."""
        platform = event.platform
        
        # Initialize counters if needed
        if platform not in self._post_count:
            self._post_count[platform] = 0
            self._success_count[platform] = 0
            self._failure_count[platform] = 0
            self._total_duration_ms[platform] = 0
        
        # Update counters
        self._post_count[platform] += 1
        self._total_duration_ms[platform] += event.duration_ms
        
        if event.status == "success":
            self._success_count[platform] += 1
        elif event.status == "failed" and event.retry_count >= event.max_retries:
            # Only count as failure if all retries exhausted
            self._failure_count[platform] += 1
    
    async def _send_to_backend(self, event: PlatformPostEvent) -> None:
        """Send usage event to Plant Backend API.
        
        Note: This is a placeholder for future implementation.
        Real implementation would send to /api/plant/usage-events endpoint.
        """
        # TODO: Implement actual API call to Plant Backend
        # For now, just log that we would send it
        logger.debug(
            f"Would send usage event to backend: "
            f"platform={event.platform} status={event.status}"
        )
        
        # Future implementation:
        # url = f"{self._plant_backend_url}/api/plant/usage-events"
        # async with httpx.AsyncClient(timeout=5.0) as client:
        #     await client.post(url, json=event.to_dict())
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for all platforms.
        
        Returns:
            Dictionary with metrics per platform
        """
        summary = {}
        
        for platform in self._post_count.keys():
            total = self._post_count[platform]
            success = self._success_count[platform]
            failure = self._failure_count[platform]
            avg_duration_ms = (
                self._total_duration_ms[platform] / total if total > 0 else 0
            )
            success_rate = (success / total * 100) if total > 0 else 0
            
            summary[platform] = {
                "total_posts": total,
                "successful_posts": success,
                "failed_posts": failure,
                "success_rate_pct": round(success_rate, 2),
                "avg_duration_ms": round(avg_duration_ms, 2),
            }
        
        return summary
    
    def reset_metrics(self) -> None:
        """Reset all metrics counters (for testing)."""
        self._post_count.clear()
        self._success_count.clear()
        self._failure_count.clear()
        self._total_duration_ms.clear()


# Global metrics collector instance
_global_collector: Optional[PlatformMetricsCollector] = None


def get_metrics_collector() -> PlatformMetricsCollector:
    """Get global metrics collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = PlatformMetricsCollector()
    return _global_collector


async def log_platform_post_event(
    customer_id: str,
    agent_id: str,
    platform: str,
    status: PostingStatus,
    duration_ms: int,
    **kwargs: Any,
) -> None:
    """Convenience function to log platform posting event.
    
    Args:
        customer_id: Customer ID
        agent_id: Agent ID
        platform: Platform name
        status: Posting status
        duration_ms: Request duration
        **kwargs: Additional event parameters
    """
    collector = get_metrics_collector()
    await collector.log_post_attempt(
        customer_id=customer_id,
        agent_id=agent_id,
        platform=platform,
        status=status,
        duration_ms=duration_ms,
        **kwargs,
    )


class TimedPlatformCall:
    """Context manager for timing platform API calls and logging metrics.
    
    Usage:
        async with TimedPlatformCall(
            customer_id="CUST-123",
            agent_id="AGENT-456",
            platform="youtube",
            correlation_id="req-xyz"
        ) as timer:
            try:
                result = await youtube_client.post_text(...)
                timer.set_success(post_id=result.post_id, post_url=result.post_url)
            except SocialPlatformError as e:
                timer.set_failure(error_code=e.error_code, error_message=e.message)
    """
    
    def __init__(
        self,
        *,
        customer_id: str,
        agent_id: str,
        platform: str,
        credential_ref: str = "",
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
        correlation_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.customer_id = customer_id
        self.agent_id = agent_id
        self.platform = platform
        self.credential_ref = credential_ref
        self.content_type = content_type
        self.content_length = content_length
        self.correlation_id = correlation_id
        self.metadata = metadata
        
        self._start_time: Optional[float] = None
        self._status: Optional[PostingStatus] = None
        self._post_id: Optional[str] = None
        self._post_url: Optional[str] = None
        self._error_code: Optional[str] = None
        self._error_message: Optional[str] = None
        self._is_transient: Optional[bool] = None
        self._retry_count: int = 0
        self._max_retries: int = 0
    
    def set_success(
        self,
        post_id: Optional[str] = None,
        post_url: Optional[str] = None,
    ) -> None:
        """Mark operation as successful."""
        self._status = PostingStatus.SUCCESS
        self._post_id = post_id
        self._post_url = post_url
    
    def set_failure(
        self,
        error_code: str,
        error_message: str,
        is_transient: bool = False,
        retry_count: int = 0,
        max_retries: int = 0,
    ) -> None:
        """Mark operation as failed."""
        self._status = PostingStatus.FAILED
        self._error_code = error_code
        self._error_message = error_message
        self._is_transient = is_transient
        self._retry_count = retry_count
        self._max_retries = max_retries
    
    def set_retrying(
        self,
        error_code: str,
        error_message: str,
        retry_count: int,
        max_retries: int,
    ) -> None:
        """Mark operation as retrying."""
        self._status = PostingStatus.RETRYING
        self._error_code = error_code
        self._error_message = error_message
        self._is_transient = True
        self._retry_count = retry_count
        self._max_retries = max_retries
    
    async def __aenter__(self) -> TimedPlatformCall:
        """Start timing."""
        self._start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and log event."""
        duration_ms = int((time.time() - self._start_time) * 1000)
        
        # If status not set, determine from exception
        if self._status is None:
            if exc_type is None:
                self._status = PostingStatus.SUCCESS
            else:
                self._status = PostingStatus.FAILED
                self._error_message = str(exc_val)
        
        # Log the event
        await log_platform_post_event(
            customer_id=self.customer_id,
            agent_id=self.agent_id,
            platform=self.platform,
            status=self._status,
            duration_ms=duration_ms,
            credential_ref=self.credential_ref,
            post_id=self._post_id,
            post_url=self._post_url,
            error_code=self._error_code,
            error_message=self._error_message,
            is_transient=self._is_transient,
            retry_count=self._retry_count,
            max_retries=self._max_retries,
            content_type=self.content_type,
            content_length=self.content_length,
            correlation_id=self.correlation_id,
            metadata=self.metadata,
        )
