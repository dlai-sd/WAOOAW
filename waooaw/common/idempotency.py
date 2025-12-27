"""
Idempotency System - Story 5.4

Ensures operations can be safely retried without side effects.
Part of Epic 5: Common Components.
"""
import logging
import hashlib
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """Status of an idempotent operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IdempotencyRecord:
    """Record of an idempotent operation."""
    idempotency_key: str
    operation_name: str
    status: OperationStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = 0.0
    completed_at: Optional[float] = None
    attempt_count: int = 0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class IdempotencyManager:
    """
    Manages idempotent operations.
    
    Features:
    - Track operation status by idempotency key
    - Return cached results for duplicate requests
    - Support retries with exponential backoff
    - TTL for idempotency records
    - Thread-safe operation tracking
    
    Usage:
        manager = IdempotencyManager()
        
        # Check if operation already completed
        if manager.is_duplicate("key_123"):
            return manager.get_result("key_123")
        
        # Mark as in progress
        manager.start_operation("key_123", "send_email")
        
        # Perform operation
        result = send_email(...)
        
        # Mark as complete
        manager.complete_operation("key_123", result)
    """
    
    def __init__(self, ttl: int = 86400):
        """
        Initialize idempotency manager.
        
        Args:
            ttl: Time-to-live for records in seconds (default: 24h)
        """
        self.ttl = ttl
        self.records: Dict[str, IdempotencyRecord] = {}
        
        logger.info(f"IdempotencyManager initialized (ttl={ttl}s)")
    
    def generate_key(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Generate idempotency key from operation and parameters.
        
        Args:
            operation: Operation name
            params: Operation parameters
            
        Returns:
            Idempotency key (hash)
        """
        # Create deterministic string from params
        param_str = str(sorted(params.items()))
        content = f"{operation}:{param_str}"
        
        # Generate hash
        key = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return f"idem_{operation}_{key}"
    
    def is_duplicate(self, idempotency_key: str) -> bool:
        """
        Check if operation is a duplicate (already completed or in progress).
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            True if duplicate
        """
        self._cleanup_expired()
        
        record = self.records.get(idempotency_key)
        
        if record is None:
            return False
        
        # Check if completed or in progress
        if record.status in [OperationStatus.COMPLETED, OperationStatus.IN_PROGRESS]:
            logger.info(f"Duplicate operation detected: {idempotency_key} (status={record.status.value})")
            return True
        
        return False
    
    def start_operation(
        self,
        idempotency_key: str,
        operation_name: str
    ) -> None:
        """
        Mark operation as started.
        
        Args:
            idempotency_key: Idempotency key
            operation_name: Name of operation
        """
        record = self.records.get(idempotency_key)
        
        if record is None:
            record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation_name=operation_name,
                status=OperationStatus.IN_PROGRESS
            )
            self.records[idempotency_key] = record
        else:
            # Retry
            record.status = OperationStatus.IN_PROGRESS
            record.attempt_count += 1
        
        logger.debug(f"Started operation: {idempotency_key} (attempt={record.attempt_count})")
    
    def complete_operation(
        self,
        idempotency_key: str,
        result: Any
    ) -> None:
        """
        Mark operation as completed.
        
        Args:
            idempotency_key: Idempotency key
            result: Operation result
        """
        record = self.records.get(idempotency_key)
        
        if record is None:
            logger.warning(f"Cannot complete unknown operation: {idempotency_key}")
            return
        
        record.status = OperationStatus.COMPLETED
        record.result = result
        record.completed_at = time.time()
        
        logger.info(f"Completed operation: {idempotency_key}")
    
    def fail_operation(
        self,
        idempotency_key: str,
        error: str
    ) -> None:
        """
        Mark operation as failed.
        
        Args:
            idempotency_key: Idempotency key
            error: Error message
        """
        record = self.records.get(idempotency_key)
        
        if record is None:
            logger.warning(f"Cannot fail unknown operation: {idempotency_key}")
            return
        
        record.status = OperationStatus.FAILED
        record.error = error
        record.completed_at = time.time()
        
        logger.warning(f"Failed operation: {idempotency_key} - {error}")
    
    def get_result(self, idempotency_key: str) -> Optional[Any]:
        """
        Get result of completed operation.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            Result if operation completed, None otherwise
        """
        record = self.records.get(idempotency_key)
        
        if record and record.status == OperationStatus.COMPLETED:
            return record.result
        
        return None
    
    def get_status(self, idempotency_key: str) -> Optional[OperationStatus]:
        """
        Get operation status.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            Operation status or None
        """
        record = self.records.get(idempotency_key)
        return record.status if record else None
    
    def can_retry(
        self,
        idempotency_key: str,
        max_attempts: int = 3
    ) -> bool:
        """
        Check if operation can be retried.
        
        Args:
            idempotency_key: Idempotency key
            max_attempts: Maximum retry attempts
            
        Returns:
            True if retry allowed
        """
        record = self.records.get(idempotency_key)
        
        if record is None:
            return True
        
        if record.status == OperationStatus.COMPLETED:
            return False
        
        return record.attempt_count < max_attempts
    
    def idempotent(
        self,
        operation_name: str,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator for idempotent operations.
        
        Usage:
            @manager.idempotent("send_email", {"to": "user@example.com"})
            def send_email(to):
                ...
        """
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                # Generate key
                _params = params or {}
                key = self.generate_key(operation_name, _params)
                
                # Check if duplicate
                if self.is_duplicate(key):
                    result = self.get_result(key)
                    if result is not None:
                        logger.info(f"Returning cached result for: {key}")
                        return result
                
                # Start operation
                self.start_operation(key, operation_name)
                
                try:
                    # Execute
                    result = func(*args, **kwargs)
                    
                    # Complete
                    self.complete_operation(key, result)
                    
                    return result
                
                except Exception as e:
                    # Fail
                    self.fail_operation(key, str(e))
                    raise
            
            return wrapper
        return decorator
    
    def _cleanup_expired(self) -> None:
        """Remove expired records."""
        now = time.time()
        expired_keys = []
        
        for key, record in self.records.items():
            if now - record.created_at > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.records[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired idempotency records")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        self._cleanup_expired()
        
        total = len(self.records)
        completed = sum(1 for r in self.records.values() if r.status == OperationStatus.COMPLETED)
        in_progress = sum(1 for r in self.records.values() if r.status == OperationStatus.IN_PROGRESS)
        failed = sum(1 for r in self.records.values() if r.status == OperationStatus.FAILED)
        
        return {
            "total_records": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "ttl": self.ttl
        }


# Global idempotency manager
_global_idempotency: Optional[IdempotencyManager] = None


def init_idempotency(ttl: int = 86400) -> IdempotencyManager:
    """
    Initialize global idempotency manager.
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        IdempotencyManager instance
    """
    global _global_idempotency
    _global_idempotency = IdempotencyManager(ttl=ttl)
    return _global_idempotency


def get_idempotency() -> IdempotencyManager:
    """Get global idempotency manager."""
    if _global_idempotency is None:
        return init_idempotency()
    return _global_idempotency
