"""
Tests for AGP2-SEC-1.3: Input Validation and Sanitization

Validates:
- SQL injection detection and prevention
- XSS detection and prevention
- Path traversal detection
- Command injection detection
- Input sanitization
- CSRF protection
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.input_validation import (
    CSRFProtection,
    InputSanitizer,
    InputValidationMiddleware,
)


# ========== SANITIZER TESTS ==========

class TestInputSanitizer:
    """Test input sanitization functions."""
    
    def test_detect_sql_injection_select(self):
        """Test SQL injection detection - SELECT."""
        assert InputSanitizer.detect_sql_injection("'; SELECT * FROM users--")
        assert InputSanitizer.detect_sql_injection("UNION SELECT password FROM users")
        assert InputSanitizer.detect_sql_injection("1' OR '1'='1")
    
    def test_detect_sql_injection_insert(self):
        """Test SQL injection detection - INSERT."""
        assert InputSanitizer.detect_sql_injection("'; INSERT INTO admins VALUES ('hacker')")
    
    def test_detect_sql_injection_drop(self):
        """Test SQL injection detection - DROP."""
        assert InputSanitizer.detect_sql_injection("'; DROP TABLE users--")
    
    def test_detect_sql_injection_safe_input(self):
        """Test safe inputs not detected as SQL injection."""
        assert not InputSanitizer.detect_sql_injection("normal text")
        assert not InputSanitizer.detect_sql_injection("user@example.com")
        assert not InputSanitizer.detect_sql_injection("John's Coffee Shop")
    
    def test_detect_xss_script_tag(self):
        """Test XSS detection - script tags."""
        assert InputSanitizer.detect_xss("<script>alert('XSS')</script>")
        assert InputSanitizer.detect_xss("<script src='evil.js'></script>")
    
    def test_detect_xss_event_handlers(self):
        """Test XSS detection - event handlers."""
        assert InputSanitizer.detect_xss("<img src=x onerror='alert(1)'>")
        assert InputSanitizer.detect_xss("<div onclick='malicious()'>")
    
    def test_detect_xss_javascript_protocol(self):
        """Test XSS detection - javascript: protocol."""
        assert InputSanitizer.detect_xss("<a href='javascript:alert(1)'>Click</a>")
    
    def test_detect_xss_iframe(self):
        """Test XSS detection - iframe injection."""
        assert InputSanitizer.detect_xss("<iframe src='evil.com'></iframe>")
    
    def test_detect_xss_safe_input(self):
        """Test safe HTML not detected as XSS."""
        assert not InputSanitizer.detect_xss("normal text")
        assert not InputSanitizer.detect_xss("<p>Safe paragraph</p>")
        assert not InputSanitizer.detect_xss("Price: $100")
    
    def test_detect_path_traversal_dot_dot_slash(self):
        """Test path traversal detection - ../ patterns."""
        assert InputSanitizer.detect_path_traversal("../../../etc/passwd")
        assert InputSanitizer.detect_path_traversal("..\\..\\windows\\system32")
    
    def test_detect_path_traversal_encoded(self):
        """Test path traversal detection - URL-encoded."""
        assert InputSanitizer.detect_path_traversal("%2e%2e/etc/passwd")
        assert InputSanitizer.detect_path_traversal("%252e%252e/secret")
    
    def test_detect_path_traversal_safe_paths(self):
        """Test safe paths not detected as traversal."""
        assert not InputSanitizer.detect_path_traversal("/api/users/123")
        assert not InputSanitizer.detect_path_traversal("files/document.pdf")
    
    def test_detect_command_injection_semicolon(self):
        """Test command injection detection - semicolon separator."""
        assert InputSanitizer.detect_command_injection("file.txt; rm -rf /")
        assert InputSanitizer.detect_command_injection("input && malicious_command")
    
    def test_detect_command_injection_backticks(self):
        """Test command injection detection - backtick substitution."""
        assert InputSanitizer.detect_command_injection("file`whoami`.txt")
    
    def test_detect_command_injection_dollar_paren(self):
        """Test command injection detection - $(command) substitution."""
        assert InputSanitizer.detect_command_injection("file$(whoami).txt")
    
    def test_detect_command_injection_safe_input(self):
        """Test safe inputs not detected as command injection."""
        assert not InputSanitizer.detect_command_injection("normal-filename.txt")
        assert not InputSanitizer.detect_command_injection("price$100")  # $ alone is OK
    
    def test_sanitize_html_escapes_tags(self):
        """Test HTML sanitization escapes tags."""
        result = InputSanitizer.sanitize_html("<script>alert('XSS')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_html_escapes_quotes(self):
        """Test HTML sanitization escapes quotes."""
        result = InputSanitizer.sanitize_html('"><img src=x>')
        assert '">' not in result
        assert "&quot;" in result
    
    def test_sanitize_filename_removes_path_separators(self):
        """Test filename sanitization removes path separators."""
        result = InputSanitizer.sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result
    
    def test_sanitize_filename_removes_null_bytes(self):
        """Test filename sanitization removes null bytes."""
        result = InputSanitizer.sanitize_filename("file\x00.txt.exe")
        assert "\x00" not in result
    
    def test_validate_input_rejects_sql_injection(self):
        """Test validate_input rejects SQL injection."""
        is_valid, error = InputSanitizer.validate_input("'; DROP TABLE users--", "username")
        assert not is_valid
        assert "SQL injection" in error
    
    def test_validate_input_rejects_xss(self):
        """Test validate_input rejects XSS."""
        is_valid, error = InputSanitizer.validate_input("<script>alert(1)</script>", "comment")
        assert not is_valid
        assert "XSS" in error
    
    def test_validate_input_rejects_path_traversal(self):
        """Test validate_input rejects path traversal."""
        is_valid, error = InputSanitizer.validate_input("../../../etc/passwd", "filename")
        assert not is_valid
        assert "path traversal" in error
    
    def test_validate_input_rejects_command_injection(self):
        """Test validate_input rejects command injection."""
        is_valid, error = InputSanitizer.validate_input("file; rm -rf /", "filename")
        assert not is_valid
        assert "command injection" in error
    
    def test_validate_input_accepts_safe_input(self):
        """Test validate_input accepts safe input."""
        is_valid, error = InputSanitizer.validate_input("John Doe", "name")
        assert is_valid
        assert error is None


# ========== MIDDLEWARE TESTS ==========

@pytest.fixture
def app_with_validation():
    """Create FastAPI app with input validation middleware."""
    app = FastAPI()
    
    app.add_middleware(InputValidationMiddleware)
    
    @app.get("/api/test")
    async def test_endpoint(query: str = ""):
        return {"message": "success", "query": query}
    
    @app.get("/api/file/{filename}")
    async def file_endpoint(filename: str):
        return {"filename": filename}
    
    return app


@pytest.fixture
def client_with_validation(app_with_validation):
    """Create test client."""
    return TestClient(app_with_validation)


class TestInputValidationMiddleware:
    """Test input validation middleware."""
    
    def test_safe_request_passes(self, client_with_validation):
        """Test safe requests pass validation."""
        response = client_with_validation.get("/api/test?query=hello")
        assert response.status_code == 200
    
    def test_sql_injection_in_query_param_blocked(self, client_with_validation):
        """Test SQL injection in query parameter is blocked."""
        response = client_with_validation.get("/api/test?query='; DROP TABLE users--")
        assert response.status_code == 400
        assert "SQL injection" in response.json()["detail"]
    
    def test_xss_in_query_param_blocked(self, client_with_validation):
        """Test XSS in query parameter is blocked."""
        response = client_with_validation.get("/api/test?query=<script>alert(1)</script>")
        assert response.status_code == 400
        assert "XSS" in response.json()["detail"]
    
    def test_path_traversal_in_url_blocked(self, client_with_validation):
        """Test path traversal in URL is blocked."""
        response = client_with_validation.get("/api/file/..%2F..%2Fetc%2Fpasswd")
        assert response.status_code == 400
        assert "path traversal" in response.json()["detail"]
    
    def test_xss_in_user_agent_blocked(self, client_with_validation):
        """Test XSS in User-Agent header is blocked."""
        response = client_with_validation.get(
            "/api/test",
            headers={"User-Agent": "<script>alert(1)</script>"}
        )
        assert response.status_code == 400
        assert "XSS" in response.json()["detail"]
    
    def test_exempt_paths_skip_validation(self, client_with_validation):
        """Test exempt paths skip validation."""
        # /docs is exempt
        response = client_with_validation.get("/docs")
        # Should not block even with malicious query (docs redirect)
        # Status may vary, but should not be 400 validation error
        assert response.status_code != 400


# ========== CSRF TESTS ==========

class TestCSRFProtection:
    """Test CSRF protection."""
    
    def test_generate_token_creates_unique_tokens(self):
        """Test token generation creates unique tokens."""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        
        assert token1 != token2
        assert len(token1) > 20  # Should be reasonably long
    
    def test_validate_token_accepts_matching_tokens(self):
        """Test validation accepts matching tokens."""
        token = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token, token)
    
    def test_validate_token_rejects_mismatched_tokens(self):
        """Test validation rejects mismatched tokens."""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        assert not CSRFProtection.validate_token(token1, token2)
    
    def test_validate_token_rejects_missing_cookie(self):
        """Test validation rejects missing cookie token."""
        token = CSRFProtection.generate_token()
        assert not CSRFProtection.validate_token(None, token)
    
    def test_validate_token_rejects_missing_header(self):
        """Test validation rejects missing header token."""
        token = CSRFProtection.generate_token()
        assert not CSRFProtection.validate_token(token, None)


# ========== INTEGRATION TESTS ==========

class TestInputValidationIntegration:
    """Integration tests for input validation."""
    
    def test_multiple_attack_types_all_blocked(self, client_with_validation):
        """Test multiple attack types are all blocked."""
        # SQL injection
        response = client_with_validation.get("/api/test?q=' OR '1'='1")
        assert response.status_code == 400
        
        # XSS
        response = client_with_validation.get("/api/test?q=<img src=x onerror=alert(1)>")
        assert response.status_code == 400
        
        # Path traversal
        response = client_with_validation.get("/api/file/../../../etc/passwd")
        assert response.status_code == 400
    
    def test_legitimate_special_characters_allowed(self, client_with_validation):
        """Test legitimate use of special characters is allowed."""
        # Email addresses
        response = client_with_validation.get("/api/test?query=user@example.com")
        assert response.status_code == 200
        
        # Apostrophes in text
        response = client_with_validation.get("/api/test?query=John's Coffee")
        assert response.status_code == 200
        
        # URLs (without javascript:)
        response = client_with_validation.get("/api/test?query=https://example.com")
        assert response.status_code == 200
