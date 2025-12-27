"""
Unit Tests for Agent Wake Protocol - Story 1.2

Tests should_wake() event filtering for BaseAgent and WowVisionPrime.
Target: 10+ test scenarios covering wake/skip conditions.
"""
import pytest
from waooaw.agents.wowvision_prime import WowVisionPrime


@pytest.fixture
def wowvision_config():
    """Mock configuration for WowVisionPrime."""
    return {
        "github_token": "test_token",
        "github_repo": "test/repo",
        "database_url": "postgresql://localhost/test",
        "anthropic_api_key": "test_key"
    }


class TestWowVisionShouldWake:
    """Test WowVisionPrime event filtering logic."""
    
    def test_wake_on_file_push(self, wowvision_config, monkeypatch):
        """Should wake for file changes in push event."""
        # Mock GitHub and DB init
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "push",
            "data": {
                "commits": [
                    {
                        "id": "abc123",
                        "author": {"name": "John Doe"},
                        "added": ["src/new_file.py"],
                        "modified": []
                    }
                ]
            }
        }
        
        assert agent.should_wake(event) is True
    
    def test_skip_readme_only_commit(self, wowvision_config, monkeypatch):
        """Should skip commits that only change README."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "push",
            "data": {
                "commits": [
                    {
                        "id": "abc123",
                        "author": {"name": "John Doe"},
                        "added": [],
                        "modified": ["README.md"]
                    }
                ]
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_skip_bot_commit(self, wowvision_config, monkeypatch):
        """Should skip commits from bots."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "push",
            "data": {
                "commits": [
                    {
                        "id": "abc123",
                        "author": {"name": "dependabot[bot]"},
                        "added": ["package.json"],
                        "modified": []
                    }
                ]
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_skip_github_config_only(self, wowvision_config, monkeypatch):
        """Should skip commits that only change .github config."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "push",
            "data": {
                "commits": [
                    {
                        "id": "abc123",
                        "author": {"name": "John Doe"},
                        "added": [],
                        "modified": [".github/workflows/test.yml"]
                    }
                ]
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_wake_on_pr_opened(self, wowvision_config, monkeypatch):
        """Should wake when PR is opened."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "pull_request",
            "action": "opened",
            "data": {
                "pull_request": {
                    "number": 42,
                    "draft": False,
                    "user": {"login": "john_doe"}
                }
            }
        }
        
        assert agent.should_wake(event) is True
    
    def test_skip_draft_pr(self, wowvision_config, monkeypatch):
        """Should skip draft PRs."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "pull_request",
            "action": "opened",
            "data": {
                "pull_request": {
                    "number": 42,
                    "draft": True,
                    "user": {"login": "john_doe"}
                }
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_skip_bot_pr(self, wowvision_config, monkeypatch):
        """Should skip PRs from bots."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "pull_request",
            "action": "opened",
            "data": {
                "pull_request": {
                    "number": 42,
                    "draft": False,
                    "user": {"login": "renovate[bot]"}
                }
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_wake_on_escalation_comment(self, wowvision_config, monkeypatch):
        """Should wake for comments on vision escalation issues."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "issue_comment",
            "action": "created",
            "data": {
                "issue": {
                    "number": 10,
                    "labels": [{"name": "vision-escalation"}, {"name": "wowvision-prime"}]
                },
                "comment": {
                    "body": "Approved - this exception is justified"
                }
            }
        }
        
        assert agent.should_wake(event) is True
    
    def test_skip_non_escalation_comment(self, wowvision_config, monkeypatch):
        """Should skip comments on non-escalation issues."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "issue_comment",
            "action": "created",
            "data": {
                "issue": {
                    "number": 10,
                    "labels": [{"name": "bug"}, {"name": "enhancement"}]
                },
                "comment": {
                    "body": "Thanks for reporting!"
                }
            }
        }
        
        assert agent.should_wake(event) is False
    
    def test_skip_unrelated_event(self, wowvision_config, monkeypatch):
        """Should skip unrelated events."""
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_github", lambda self: None)
        monkeypatch.setattr("waooaw.agents.base_agent.WAAOOWAgent._init_database", lambda self: None)
        
        agent = WowVisionPrime(wowvision_config)
        
        event = {
            "event_type": "star",
            "action": "created",
            "data": {}
        }
        
        assert agent.should_wake(event) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
