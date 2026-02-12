"""
AGP2-SEC-1.3: Input Validation and Sanitization Middleware

Prevents:
- SQL injection attacks
- XSS (Cross-Site Scripting) attacks  
- Command injection
- Path traversal
- CSRF (Cross-Site Request Forgery)

Implements:
- Request body validation
- Query parameter sanitization
- Header validation
- File upload validation
- CSRF token validation
"""

from __future__ import annotations

import html
import re
from typing import Any, Callable, Optional
from urllib.parse import unquote

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class InputSanitizer:
    """
    Sanitize user inputs to prevent injection attacks.
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(--|\#|/\*)",  # SQL comments
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b)",  # Stacked queries
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers (onclick, onerror, etc.)
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"%252e%252e",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",  # Shell command separators
        r"\$\([^\)]*\)",  # Command substitution
        r"`[^`]*`",  # Backtick command substitution
    ]
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection attempt."""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """Detect potential XSS attempt."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_path_traversal(cls, value: str) -> bool:
        """Detect potential path traversal attempt."""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_command_injection(cls, value: str) -> bool:
        """Detect potential command injection attempt."""
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                return True
        return False
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Escape HTML to prevent XSS."""
        return html.escape(value)
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")
        # Remove parent directory references
        filename = filename.replace("..", "")
        # Remove null bytes
        filename = filename.replace("\x00", "")
        return filename
    
    @classmethod
    def validate_input(cls, value: Any, field_name: str = "input") -> tuple[bool, Optional[str]]:
        """
        Validate input for common injection attacks.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(value, str):
            return True, None  # Non-string values handled by Pydantic
        
        # Check SQL injection
        if cls.detect_sql_injection(value):
            return False, f"{field_name} contains potential SQL injection"
        
        # Check XSS
        if cls.detect_xss(value):
            return False, f"{field_name} contains potential XSS"
        
        # Check path traversal
        if cls.detect_path_traversal(value):
            return False, f"{field_name} contains potential path traversal"
        
        # Check command injection
        if cls.detect_command_injection(value):
            return False, f"{field_name} contains potential command injection"
        
        return True, None


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for input validation and sanitization.
    
    Features:
    - Validates query parameters
    - Validates request headers
    - Detects SQL injection
    - Detects XSS
    - Detects path traversal
    - Detects command injection
    
    Note: Request body validation handled by Pydantic models.
    """
    
    def __init__(
        self,
        app,
        *,
        enable_sql_injection_detection: bool = True,
        enable_xss_detection: bool = True,
        enable_path_traversal_detection: bool = True,
        enable_command_injection_detection: bool = True,
        exempt_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.enable_sql_injection = enable_sql_injection_detection
        self.enable_xss = enable_xss_detection
        self.enable_path_traversal = enable_path_traversal_detection
        self.enable_command_injection = enable_command_injection_detection
        self.exempt_paths = exempt_paths or ["/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request inputs."""
        # Skip validation for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Validate query parameters
        for param_name, param_value in request.query_params.items():
            is_valid, error = InputSanitizer.validate_input(param_value, f"Query parameter '{param_name}'")
            if not is_valid:
                return self._validation_error_response(error)
        
        # Validate path parameters (URL-decoded)
        path = unquote(request.url.path)
        if InputSanitizer.detect_path_traversal(path):
            return self._validation_error_response("URL path contains path traversal attempt")
        
        # Validate unsafe headers (User-Agent, Referer can contain malicious data)
        user_agent = request.headers.get("User-Agent", "")
        if self.enable_xss and InputSanitizer.detect_xss(user_agent):
            return self._validation_error_response("User-Agent header contains potential XSS")
        
        # Process request
        return await call_next(request)
    
    def _validation_error_response(self, error_message: str) -> JSONResponse:
        """Create validation error response."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "type": "https://waooaw.com/errors/input-validation-failed",
                "title": "Input Validation Failed",
                "status": 400,
                "detail": error_message,
                "instance": "/",
            }
        )


class CSRFProtection:
    """
    CSRF (Cross-Site Request Forgery) protection.
    
    Implements double-submit cookie pattern:
    1. Server generates CSRF token
    2. Token sent as cookie and expected in header
    3. Server validates token matches
    """
    
    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(cookie_token: Optional[str], header_token: Optional[str]) -> bool:
        """Validate CSRF token matches."""
        if not cookie_token or not header_token:
            return False
        return cookie_token == header_token
