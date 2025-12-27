"""
Integration Test Harness - Story 6.2

Framework for testing interactions between multiple components.
Part of Epic 6: Testing Infrastructure.
"""
import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class IntegrationTestHarness:
    """
    Harness for integration testing.
    
    Features:
    - Set up test environment
    - Mock external dependencies
    - Manage test data
    - Clean up resources
    - Coordinate multi-component tests
    """
    
    def __init__(self):
        """Initialize test harness."""
        self.temp_dirs: List[str] = []
        self.temp_files: List[str] = []
        self.cleanup_callbacks: List[callable] = []
        
    def setup(self) -> None:
        """Set up test environment."""
        pass
    
    def teardown(self) -> None:
        """Clean up test environment."""
        # Remove temp files
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception:
                pass
        
        # Remove temp directories
        for dir_path in self.temp_dirs:
            try:
                if os.path.exists(dir_path):
                    import shutil
                    shutil.rmtree(dir_path)
            except Exception:
                pass
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass
    
    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> str:
        """
        Create temporary file.
        
        Args:
            content: File content
            suffix: File suffix
            
        Returns:
            File path
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        
        if content:
            os.write(fd, content.encode())
        
        os.close(fd)
        
        self.temp_files.append(path)
        return path
    
    def create_temp_dir(self) -> str:
        """
        Create temporary directory.
        
        Returns:
            Directory path
        """
        path = tempfile.mkdtemp()
        self.temp_dirs.append(path)
        return path
    
    def register_cleanup(self, callback: callable) -> None:
        """
        Register cleanup callback.
        
        Args:
            callback: Function to call on teardown
        """
        self.cleanup_callbacks.append(callback)


@pytest.fixture
def test_harness():
    """Pytest fixture for test harness."""
    harness = IntegrationTestHarness()
    harness.setup()
    
    yield harness
    
    harness.teardown()


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "environment": "test",
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "logging": {
            "level": "DEBUG",
            "format": "json"
        }
    }


@pytest.fixture
def mock_secrets():
    """Mock secrets for testing."""
    return {
        "api_key": "test_api_key_12345",
        "github_token": "ghp_test_token",
        "claude_api_key": "sk-ant-test-key"
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class MockRedisClient:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.streams: Dict[str, List[Dict]] = {}
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        """Set key-value."""
        self.data[key] = value
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value."""
        return self.data.get(key)
    
    async def delete(self, key: str) -> None:
        """Delete key."""
        if key in self.data:
            del self.data[key]
    
    async def xadd(self, stream: str, fields: Dict) -> str:
        """Add to stream."""
        if stream not in self.streams:
            self.streams[stream] = []
        
        entry_id = f"{len(self.streams[stream])}-0"
        self.streams[stream].append({"id": entry_id, "data": fields})
        
        return entry_id
    
    async def xread(self, streams: Dict[str, str], count: int = 10, block: Optional[int] = None):
        """Read from streams."""
        results = []
        
        for stream_name, last_id in streams.items():
            if stream_name in self.streams:
                # Simple implementation - return all
                results.append((stream_name, self.streams[stream_name]))
        
        return results


@pytest.fixture
def mock_redis():
    """Mock Redis client fixture."""
    return MockRedisClient()


class MockGitHubAPI:
    """Mock GitHub API for testing."""
    
    def __init__(self):
        self.issues: Dict[int, Dict] = {}
        self.prs: Dict[int, Dict] = {}
        self.issue_counter = 1
        self.pr_counter = 1
    
    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Dict:
        """Create issue."""
        issue_number = self.issue_counter
        self.issue_counter += 1
        
        issue = {
            "number": issue_number,
            "title": title,
            "body": body,
            "labels": labels or [],
            "state": "open",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        self.issues[issue_number] = issue
        return issue
    
    def get_issue(self, number: int) -> Optional[Dict]:
        """Get issue."""
        return self.issues.get(number)
    
    def create_pr(self, title: str, body: str, head: str, base: str = "main") -> Dict:
        """Create PR."""
        pr_number = self.pr_counter
        self.pr_counter += 1
        
        pr = {
            "number": pr_number,
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "state": "open",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        self.prs[pr_number] = pr
        return pr
    
    def get_pr(self, number: int) -> Optional[Dict]:
        """Get PR."""
        return self.prs.get(number)


@pytest.fixture
def mock_github():
    """Mock GitHub API fixture."""
    return MockGitHubAPI()


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.responses: List[str] = []
        self.default_response = "This is a test response from the mock LLM."
    
    def add_response(self, response: str) -> None:
        """Add canned response."""
        self.responses.append(response)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response."""
        self.call_count += 1
        self.last_prompt = prompt
        
        if self.responses:
            return self.responses.pop(0)
        
        return self.default_response
    
    def reset(self) -> None:
        """Reset state."""
        self.call_count = 0
        self.last_prompt = None
        self.responses = []


@pytest.fixture
def mock_llm():
    """Mock LLM client fixture."""
    return MockLLMClient()


# Helper functions for integration tests

def assert_eventually(condition: callable, timeout: float = 5.0, interval: float = 0.1) -> None:
    """
    Assert that condition becomes true within timeout.
    
    Args:
        condition: Function returning bool
        timeout: Timeout in seconds
        interval: Check interval
    """
    import time
    
    start = time.time()
    
    while time.time() - start < timeout:
        if condition():
            return
        
        time.sleep(interval)
    
    raise AssertionError(f"Condition not met within {timeout}s")


async def assert_eventually_async(condition: callable, timeout: float = 5.0, interval: float = 0.1) -> None:
    """
    Async version of assert_eventually.
    
    Args:
        condition: Async function returning bool
        timeout: Timeout in seconds
        interval: Check interval
    """
    start = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start < timeout:
        if await condition():
            return
        
        await asyncio.sleep(interval)
    
    raise AssertionError(f"Condition not met within {timeout}s")


def create_test_config_file(harness: IntegrationTestHarness, config: Dict[str, Any]) -> str:
    """
    Create test config file.
    
    Args:
        harness: Test harness
        config: Config dict
        
    Returns:
        File path
    """
    import yaml
    
    content = yaml.dump(config, default_flow_style=False)
    return harness.create_temp_file(content, suffix=".yaml")


def create_test_env_file(harness: IntegrationTestHarness, env_vars: Dict[str, str]) -> str:
    """
    Create test .env file.
    
    Args:
        harness: Test harness
        env_vars: Environment variables
        
    Returns:
        File path
    """
    lines = [f"{key}={value}" for key, value in env_vars.items()]
    content = "\n".join(lines)
    
    return harness.create_temp_file(content, suffix=".env")
