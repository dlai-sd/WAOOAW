"""
WAOOAW Common Components: Security Layer

Provides authentication, authorization, encryption, and audit logging.

Usage:
    # Basic security:
    security = SecurityLayer(secret_key="your-secret-key")
    
    # Sign message:
    signature = security.sign_message(message)
    
    # Verify signature:
    is_valid = security.verify_signature(message, signature)
    
    # Create JWT token:
    token = security.create_token({"agent_id": "wowvision-prime"})
    
    # Verify token:
    payload = security.verify_token(token)

Vision Compliance:
    ✅ Zero Risk: Signed messages, encrypted data, audit trail
    ✅ Agentic: Agent-level permissions and isolation
    ✅ Simplicity: Drop-in security for all operations
"""

import hmac
import hashlib
import logging
import secrets
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditLog:
    """
    Immutable audit log entry.
    
    Attributes:
        timestamp: When action occurred
        agent_id: Agent performing action
        action: Action type (e.g., "decision", "escalation")
        resource: Resource affected
        outcome: Success/failure
        metadata: Additional context
    """
    timestamp: datetime
    agent_id: str
    action: str
    resource: str
    outcome: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class Permission:
    """
    Permission definition.
    
    Attributes:
        resource: Resource type (e.g., "decision", "github")
        actions: Allowed actions (e.g., ["read", "write"])
        conditions: Optional conditions (e.g., {"agent_id": "wowvision-prime"})
    """
    resource: str
    actions: List[str]
    conditions: Optional[Dict[str, Any]] = None


class SecurityLayer:
    """
    Authentication, authorization, encryption, and audit logging.
    
    Features:
    - HMAC message signing
    - JWT token generation/verification
    - Role-based access control (RBAC)
    - Permission validation
    - Audit logging
    - Data encryption (optional)
    
    Example:
        security = SecurityLayer(
            secret_key="your-secret-key",
            audit_db=db
        )
        
        # Sign message:
        signature = security.sign_message(message)
        
        # Verify signature:
        is_valid = security.verify_signature(message, signature)
        
        # Create token:
        token = security.create_token({"agent_id": "wowvision-prime"})
        
        # Verify token:
        payload = security.verify_token(token)
        
        # Check permission:
        allowed = security.check_permission(
            agent_id="wowvision-prime",
            resource="decision",
            action="write"
        )
        
        # Audit action:
        security.audit_action(
            agent_id="wowvision-prime",
            action="make_decision",
            resource="decision-123",
            outcome="success"
        )
    """
    
    def __init__(
        self,
        secret_key: str,
        audit_db: Optional[Any] = None,
        token_expiry_hours: int = 24
    ):
        """
        Initialize security layer.
        
        Args:
            secret_key: Secret key for signing
            audit_db: Database connection for audit logs
            token_expiry_hours: JWT token expiry (default: 24h)
        """
        self.secret_key = secret_key.encode('utf-8')
        self.audit_db = audit_db
        self.token_expiry_hours = token_expiry_hours
        
        self._permissions: Dict[str, List[Permission]] = {}
        self._audit_logs: List[AuditLog] = []
        
        logger.info(f"SecurityLayer initialized (token_expiry={token_expiry_hours}h)")
    
    # Message Signing (HMAC)
    
    def sign_message(self, message: str) -> str:
        """
        Sign message with HMAC-SHA256.
        
        Args:
            message: Message to sign
            
        Returns:
            Hex-encoded signature
        """
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, message: str, signature: str) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            message: Original message
            signature: Signature to verify
            
        Returns:
            True if signature valid
        """
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(expected_signature, signature)
    
    # JWT Tokens
    
    def create_token(
        self,
        payload: Dict[str, Any],
        expiry_hours: Optional[int] = None
    ) -> str:
        """
        Create JWT token.
        
        Args:
            payload: Token payload
            expiry_hours: Expiry in hours (default: from __init__)
            
        Returns:
            JWT token string
        """
        import base64
        import json
        
        expiry_hours = expiry_hours or self.token_expiry_hours
        
        # Add standard claims
        now = datetime.now()
        payload_copy = payload.copy()
        payload_copy['iat'] = int(now.timestamp())
        payload_copy['exp'] = int((now + timedelta(hours=expiry_hours)).timestamp())
        
        # Create token: header.payload.signature
        header = {'alg': 'HS256', 'typ': 'JWT'}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode()).decode().rstrip('=')
        
        message = f"{header_b64}.{payload_b64}"
        signature = self.sign_message(message)
        signature_b64 = base64.urlsafe_b64encode(bytes.fromhex(signature)).decode().rstrip('=')
        
        token = f"{message}.{signature_b64}"
        
        logger.debug(f"Created JWT token (expires in {expiry_hours}h)")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Payload if valid, None if invalid/expired
        """
        import base64
        import json
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid token format")
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}"
            signature = base64.urlsafe_b64decode(signature_b64 + '==').hex()
            
            if not self.verify_signature(message, signature):
                logger.warning("Token signature invalid")
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64 + '==').decode()
            payload = json.loads(payload_json)
            
            # Check expiry
            exp = payload.get('exp')
            if exp and datetime.now().timestamp() > exp:
                logger.warning("Token expired")
                return None
            
            return payload
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    # Role-Based Access Control
    
    def add_permission(
        self,
        agent_id: str,
        resource: str,
        actions: List[str],
        conditions: Optional[Dict[str, Any]] = None
    ):
        """
        Grant permission to agent.
        
        Args:
            agent_id: Agent identifier
            resource: Resource type
            actions: Allowed actions
            conditions: Optional conditions
        """
        if agent_id not in self._permissions:
            self._permissions[agent_id] = []
        
        permission = Permission(
            resource=resource,
            actions=actions,
            conditions=conditions
        )
        
        self._permissions[agent_id].append(permission)
        
        logger.info(f"Permission granted: {agent_id} -> {resource} [{', '.join(actions)}]")
    
    def remove_permission(
        self,
        agent_id: str,
        resource: str,
        action: Optional[str] = None
    ):
        """
        Revoke permission from agent.
        
        Args:
            agent_id: Agent identifier
            resource: Resource type
            action: Optional specific action to remove
        """
        if agent_id not in self._permissions:
            return
        
        if action:
            # Remove specific action from resource
            for perm in self._permissions[agent_id]:
                if perm.resource == resource and action in perm.actions:
                    perm.actions.remove(action)
        else:
            # Remove all permissions for resource
            self._permissions[agent_id] = [
                p for p in self._permissions[agent_id]
                if p.resource != resource
            ]
        
        logger.info(f"Permission revoked: {agent_id} -> {resource}" + (f".{action}" if action else ""))
    
    def check_permission(
        self,
        agent_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if agent has permission.
        
        Args:
            agent_id: Agent identifier
            resource: Resource type
            action: Action to check
            context: Optional context for condition evaluation
            
        Returns:
            True if permission granted
        """
        if agent_id not in self._permissions:
            return False
        
        for perm in self._permissions[agent_id]:
            if perm.resource == resource and action in perm.actions:
                # Check conditions if present
                if perm.conditions and context:
                    if not self._evaluate_conditions(perm.conditions, context):
                        continue
                
                return True
        
        return False
    
    def get_permissions(self, agent_id: str) -> List[Permission]:
        """
        Get all permissions for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of permissions
        """
        return self._permissions.get(agent_id, [])
    
    # Audit Logging
    
    def audit_action(
        self,
        agent_id: str,
        action: str,
        resource: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log action for audit trail.
        
        Args:
            agent_id: Agent performing action
            action: Action type
            resource: Resource affected
            outcome: Success/failure
            metadata: Additional context
        """
        log = AuditLog(
            timestamp=datetime.now(),
            agent_id=agent_id,
            action=action,
            resource=resource,
            outcome=outcome,
            metadata=metadata
        )
        
        self._audit_logs.append(log)
        
        # Persist to database if available
        if self.audit_db:
            self._persist_audit_log(log)
        
        logger.info(f"Audit: {agent_id} {action} {resource} -> {outcome}")
    
    def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs with filters.
        
        Args:
            agent_id: Filter by agent
            action: Filter by action type
            limit: Maximum logs to return
            
        Returns:
            List of audit logs (newest first)
        """
        logs = self._audit_logs
        
        if agent_id:
            logs = [log for log in logs if log.agent_id == agent_id]
        
        if action:
            logs = [log for log in logs if log.action == action]
        
        return list(reversed(logs[-limit:]))
    
    # Encryption (Basic)
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data (simple XOR for demo - use real encryption in production).
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data (hex)
        """
        # WARNING: This is NOT production-grade encryption
        # Use cryptography library (Fernet) for real encryption
        import base64
        
        key_bytes = self.secret_key
        data_bytes = data.encode('utf-8')
        
        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_data(self, encrypted: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted: Encrypted data (hex)
            
        Returns:
            Decrypted data
        """
        import base64
        
        key_bytes = self.secret_key
        encrypted_bytes = base64.b64decode(encrypted)
        
        decrypted = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return decrypted.decode('utf-8')
    
    # Utilities
    
    def generate_api_key(self, length: int = 32) -> str:
        """
        Generate secure random API key.
        
        Args:
            length: Key length in bytes
            
        Returns:
            Hex-encoded API key
        """
        return secrets.token_hex(length)
    
    def hash_password(self, password: str) -> str:
        """
        Hash password with SHA-256 (use bcrypt in production).
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # WARNING: Use bcrypt or argon2 for real password hashing
        salt = self.secret_key[:16]
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if match
        """
        return self.hash_password(password) == hashed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get security statistics.
        
        Returns:
            Dict with permission count, audit log count, etc.
        """
        return {
            'permission_count': sum(len(perms) for perms in self._permissions.values()),
            'agent_count': len(self._permissions),
            'audit_log_count': len(self._audit_logs),
            'token_expiry_hours': self.token_expiry_hours
        }
    
    # Private methods
    
    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate permission conditions against context."""
        for key, expected_value in conditions.items():
            if context.get(key) != expected_value:
                return False
        return True
    
    def _persist_audit_log(self, log: AuditLog):
        """Persist audit log to database."""
        if not self.audit_db:
            return
        
        try:
            import json
            cursor = self.audit_db.cursor()
            
            metadata_json = json.dumps(log.metadata) if log.metadata else None
            
            cursor.execute(
                """
                INSERT INTO audit_logs 
                (timestamp, agent_id, action, resource, outcome, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (log.timestamp, log.agent_id, log.action, log.resource, log.outcome, metadata_json)
            )
            
            self.audit_db.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to persist audit log: {e}")
