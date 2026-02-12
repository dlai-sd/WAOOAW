"""
AGP2-SEC-1.4: Comprehensive Audit Logging Enhancement

Implements:
- Logging of all sensitive operations
- Immutable append-only audit trail
- PII redaction and hashing for compliance
- Structured audit events for all security-critical operations
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.security_audit import (
    SecurityAuditRecord,
    get_security_audit_store,
)


class SensitiveOperationType(str, Enum):
    """Types of sensitive operations that must be audited."""
    
    # Authentication and authorization
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    
    # Credential management
    CREDENTIAL_CREATED = "credential_created"
    CREDENTIAL_UPDATED = "credential_updated"
    CREDENTIAL_DELETED = "credential_deleted"
    CREDENTIAL_ACCESSED = "credential_accessed"
    CREDENTIAL_ENCRYPTED = "credential_encrypted"
    CREDENTIAL_DECRYPTED = "credential_decrypted"
    
    # Agent operations
    AGENT_HIRED = "agent_hired"
    AGENT_FIRED = "agent_fired"
    AGENT_CONFIG_CHANGED = "agent_config_changed"
    GOAL_CREATED = "goal_created"
    GOAL_TRIGGERED = "goal_triggered"
    GOAL_DELETED = "goal_deleted"
    
    # Approval workflow
    DELIVERABLE_CREATED = "deliverable_created"
    DELIVERABLE_APPROVED = "deliverable_approved"
    DELIVERABLE_REJECTED = "deliverable_rejected"
    EXTERNAL_ACTION_EXECUTED = "external_action_executed"
    
    # Trading operations
    TRADE_INTENT = "trade_intent"
    TRADE_EXECUTED = "trade_executed"
    TRADE_FAILED = "trade_failed"
    POSITION_CLOSED = "position_closed"
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    OPS_OVERRIDE_USED = "ops_override_used"
    
    # Platform integrations
    PLATFORM_POST = "platform_post"
    PLATFORM_AUTH_FAILED = "platform_auth_failed"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT_DETECTED = "invalid_input_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    
    # Data access
    CUSTOMER_DATA_ACCESSED = "customer_data_accessed"
    PII_ACCESSED = "pii_accessed"
    BULK_DATA_EXPORT = "bulk_data_export"


class PIIRedactor:
    """Redact or hash PII for GDPR compliance."""
    
    # PII patterns for detection
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\+?[1-9]\d{1,14}\b')  # E.164 format
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{13,19}\b')
    IP_ADDRESS_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    
    # PII field names (case-insensitive)
    PII_FIELD_NAMES = {
        "email", "phone", "phone_number", "credit_card", "card_number",
        "ssn", "passport", "license", "address", "streetaddress",
        "api_key", "api_secret", "password", "token", "access_token",
        "refresh_token", "private_key", "secret_key"
    }
    
    # Fields that should NEVER be hashed (always redacted completely)
    ALWAYS_REDACT_FIELDS = {"password", "api_secret", "private_key", "secret_key"}
    
    @staticmethod
    def hash_pii(value: str) -> str:
        """Hash PII value for audit trail (one-way).
        
        Args:
            value: PII value to hash
            
        Returns:
            SHA256 hash prefixed with "hashed:"
        """
        hashed = hashlib.sha256(value.encode('utf-8')).hexdigest()
        return f"hashed:{hashed[:16]}"  # First 16 chars for readability
    
    @staticmethod
    def redact_pii(value: str) -> str:
        """Redact PII value completely.
        
        Args:
            value: PII value to redact
            
        Returns:
            Redacted string like "REDACTED_EMAIL"
        """
        if PIIRedactor.EMAIL_PATTERN.match(value):
            return "[REDACTED_EMAIL]"
        elif PIIRedactor.PHONE_PATTERN.match(value):
            return "[REDACTED_PHONE]"
        elif PIIRedactor.CREDIT_CARD_PATTERN.match(value):
            return "[REDACTED_CARD]"
        else:
            return "[REDACTED]"
    
    @staticmethod
    def redact_dict(data: Dict[str, Any], hash_instead: bool = False) -> Dict[str, Any]:
        """Recursively redact PII from dictionary.
        
        Args:
            data: Dictionary possibly containing PII
            hash_instead: If True, hash PII; if False, redact completely
            
        Returns:
            Dictionary with PII redacted or hashed
        """
        result = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field name indicates PII
            if any(pii_field in key_lower for pii_field in PIIRedactor.PII_FIELD_NAMES):
                # Some fields should ALWAYS be redacted, never hashed
                if any(always_redact in key_lower for always_redact in PIIRedactor.ALWAYS_REDACT_FIELDS):
                    result[key] = "[REDACTED]"
                elif hash_instead and isinstance(value, str):
                    result[key] = PIIRedactor.hash_pii(value)
                else:
                    result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = PIIRedactor.redact_dict(value, hash_instead)
            elif isinstance(value, list):
                result[key] = [
                    PIIRedactor.redact_dict(item, hash_instead) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Check string patterns (email, phone, etc.)
                if PIIRedactor.EMAIL_PATTERN.search(value):
                    result[key] = value if not hash_instead else PIIRedactor.hash_pii(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result


class ComprehensiveAuditLogger:
    """Comprehensive audit logger for all sensitive operations.
    
    Features:
    - Immutable append-only log
    - PII redaction/hashing for compliance
    - Structured events for all security-critical operations
    - Correlation IDs for request tracing
    """
    
    def __init__(self):
        self._store = get_security_audit_store()
    
    async def log_sensitive_operation(
        self,
        *,
        operation_type: SensitiveOperationType,
        actor_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log a sensitive operation to the audit trail.
        
        Args:
            operation_type: Type of sensitive operation
            actor_id: ID of user/agent performing operation
            customer_id: ID of customer (if applicable)
            resource_id: ID of resource affected
            resource_type: Type of resource (agent, goal, credential, etc.)
            success: Whether operation succeeded
            failure_reason: Reason for failure (if success=False)
            metadata: Additional context (will be PII-redacted)
            ip_address: Source IP address
            user_agent: User agent string
            correlation_id: Request correlation ID
        """
        # Redact PII from metadata
        safe_metadata = {}
        if metadata:
            safe_metadata = PIIRedactor.redact_dict(metadata, hash_instead=True)
        
        # Add operation details to metadata
        safe_metadata["operation_type"] = operation_type.value
        if resource_id:
            safe_metadata["resource_id"] = resource_id
        if resource_type:
            safe_metadata["resource_type"] = resource_type
        if failure_reason:
            safe_metadata["failure_reason"] = failure_reason
        if correlation_id:
            safe_metadata["correlation_id"] = correlation_id
        if actor_id:
            # Hash actor_id for privacy
            safe_metadata["actor_id"] = PIIRedactor.hash_pii(actor_id)
        if customer_id:
            # Hash customer_id for privacy
            safe_metadata["customer_id"] = PIIRedactor.hash_pii(customer_id)
        
        # Create audit record
        record = SecurityAuditRecord(
            event_type=operation_type.value,
            email=actor_id,  # Will be hashed in storage
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            detail=f"{operation_type.value} {'succeeded' if success else 'failed'}",
            metadata=safe_metadata,
        )
        
        # Append to immutable store
        self._store.append(record)
    
    async def log_authentication(
        self,
        *,
        actor_id: str,
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        auth_method: str = "password",
    ) -> None:
        """Log authentication attempt."""
        await self.log_sensitive_operation(
            operation_type=SensitiveOperationType.LOGIN,
            actor_id=actor_id,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"auth_method": auth_method},
        )
    
    async def log_credential_operation(
        self,
        *,
        operation: str,  # created, updated, deleted, accessed
        customer_id: str,
        credential_id: str,
        credential_type: str,
        actor_id: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Log credential management operation."""
        op_type_map = {
            "created": SensitiveOperationType.CREDENTIAL_CREATED,
            "updated": SensitiveOperationType.CREDENTIAL_UPDATED,
            "deleted": SensitiveOperationType.CREDENTIAL_DELETED,
            "accessed": SensitiveOperationType.CREDENTIAL_ACCESSED,
            "encrypted": SensitiveOperationType.CREDENTIAL_ENCRYPTED,
            "decrypted": SensitiveOperationType.CREDENTIAL_DECRYPTED,
        }
        
        await self.log_sensitive_operation(
            operation_type=op_type_map.get(operation, SensitiveOperationType.CREDENTIAL_ACCESSED),
            actor_id=actor_id,
            customer_id=customer_id,
            resource_id=credential_id,
            resource_type="credential",
            success=success,
            metadata={"credential_type": credential_type},
        )
    
    async def log_agent_operation(
        self,
        *,
        operation: str,  # hired, fired, config_changed
        customer_id: str,
        agent_id: str,
        agent_type: str,
        actor_id: Optional[str] = None,
        config_changes: Optional[Dict] = None,
    ) -> None:
        """Log agent lifecycle operation."""
        op_type_map = {
            "hired": SensitiveOperationType.AGENT_HIRED,
            "fired": SensitiveOperationType.AGENT_FIRED,
            "config_changed": SensitiveOperationType.AGENT_CONFIG_CHANGED,
        }
        
        metadata = {"agent_type": agent_type}
        if config_changes:
            metadata["config_changes"] = config_changes
        
        await self.log_sensitive_operation(
            operation_type=op_type_map[operation],
            actor_id=actor_id,
            customer_id=customer_id,
            resource_id=agent_id,
            resource_type="agent",
            metadata=metadata,
        )
    
    async def log_approval_workflow(
        self,
        *,
        action: str,  # created, approved, rejected
        customer_id: str,
        deliverable_id: str,
        deliverable_type: str,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log approval workflow event."""
        op_type_map = {
            "created": SensitiveOperationType.DELIVERABLE_CREATED,
            "approved": SensitiveOperationType.DELIVERABLE_APPROVED,
            "rejected": SensitiveOperationType.DELIVERABLE_REJECTED,
        }
        
        metadata = {"deliverable_type": deliverable_type}
        if reason:
            metadata["reason"] = reason
        
        await self.log_sensitive_operation(
            operation_type=op_type_map[action],
            actor_id=actor_id,
            customer_id=customer_id,
            resource_id=deliverable_id,
            resource_type="deliverable",
            metadata=metadata,
        )
    
    async def log_security_event(
        self,
        *,
        event_type: SensitiveOperationType,
        details: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        actor_id: Optional[str] = None,
        severity: str = "medium",
    ) -> None:
        """Log security-related event (injection attempt, rate limit, etc.)."""
        await self.log_sensitive_operation(
            operation_type=event_type,
            actor_id=actor_id,
            success=False,  # Security events are failed attempts
            failure_reason=details,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"severity": severity},
        )
    
    def get_audit_trail(
        self,
        *,
        operation_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail records.
        
        Args:
            operation_type: Filter by operation type
            customer_id: Filter by customer ID (will be hashed for query)
            limit: Maximum records to return
            
        Returns:
            List of audit records (PII-redacted)
        """
        # Hash customer_id if provided (since it's stored hashed)
        email_filter = None
        if customer_id:
            email_filter = customer_id  # Will be hashed by store
        
        records = self._store.list_records(
            event_type=operation_type,
            email=email_filter,
            limit=limit,
        )
        
        # Convert to dicts and ensure PII redaction
        return [
            PIIRedactor.redact_dict(record.model_dump(), hash_instead=False)
            for record in records
        ]


# Singleton instance
_audit_logger: Optional[ComprehensiveAuditLogger] = None


def get_audit_logger() -> ComprehensiveAuditLogger:
    """Get the singleton audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = ComprehensiveAuditLogger()
    return _audit_logger
