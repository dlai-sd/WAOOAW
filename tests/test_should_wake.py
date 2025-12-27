"""
Unit tests for should_wake() Filter (Story 1.2)

Tests WowVision Prime's event filtering logic to determine
when the agent should wake up vs stay asleep.

Wake for:
- File creations (except README.md, configs, locks)
- PR opened
- Issue comments (escalation responses only)
- Commits (except bot commits)

Skip:
- README.md edits
- Config files (.yaml, .json, etc.)
- Lock files
- Bot commits
- File deletions
- Unknown events

Target: 10+ test scenarios
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.agents.event_types import (
    EVENT_FILE_CREATED,
    EVENT_FILE_UPDATED,
    EVENT_FILE_DELETED,
    EVENT_PR_OPENED,
    EVENT_PR_CLOSED,
    EVENT_ISSUE_COMMENT,
    EVENT_COMMIT_PUSHED,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def wowvision_agent():
    """Minimal WowVision Prime agent - just need should_wake() method"""
    # Create a mock agent object with just the should_wake method
    agent = MagicMock(spec=WowVisionPrime)
    agent.agent_id = "WowVision-Prime"
    
    # Bind the actual should_wake method from WowVisionPrime class
    # This way we test the real implementation, not a mock
    agent.should_wake = WowVisionPrime.should_wake.__get__(agent, WowVisionPrime)
    
    return agent


# ============================================================================
# TEST: WAKE FOR FILE CREATIONS
# ============================================================================

def test_wake_for_python_file_creation(wowvision_agent):
    """Test wakes for Python file creation"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "app/main.py",
            "commit_sha": "abc123",
            "author": "developer@example.com"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_wake_for_html_file_creation(wowvision_agent):
    """Test wakes for HTML file creation"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "frontend/index.html",
            "commit_sha": "def456"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_wake_for_markdown_doc_creation(wowvision_agent):
    """Test wakes for markdown documentation (non-README)"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "docs/architecture.md"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


# ============================================================================
# TEST: SKIP README.MD
# ============================================================================

def test_skip_readme_creation(wowvision_agent):
    """Test skips README.md creation"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "README.md"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_readme_in_subdirectory(wowvision_agent):
    """Test skips README.md in subdirectories"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "docs/subproject/README.md"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: SKIP CONFIG FILES
# ============================================================================

def test_skip_yaml_config(wowvision_agent):
    """Test skips YAML config files"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "config.yaml"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_json_config(wowvision_agent):
    """Test skips JSON config files"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "package.json"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_env_file(wowvision_agent):
    """Test skips .env files"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": ".env.example"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_toml_config(wowvision_agent):
    """Test skips TOML config files"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "pyproject.toml"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: SKIP LOCK FILES
# ============================================================================

def test_skip_package_lock(wowvision_agent):
    """Test skips package-lock.json"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "package-lock.json"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_poetry_lock(wowvision_agent):
    """Test skips poetry.lock"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {
            "file_path": "poetry.lock"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: WAKE FOR FILE UPDATES
# ============================================================================

def test_wake_for_python_file_update(wowvision_agent):
    """Test wakes for Python file update"""
    event = {
        "event_type": EVENT_FILE_UPDATED,
        "payload": {
            "file_path": "app/models.py"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_skip_readme_update(wowvision_agent):
    """Test skips README.md update"""
    event = {
        "event_type": EVENT_FILE_UPDATED,
        "payload": {
            "file_path": "README.md"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: WAKE FOR PR OPENED
# ============================================================================

def test_wake_for_pr_opened(wowvision_agent):
    """Test wakes for PR opened"""
    event = {
        "event_type": EVENT_PR_OPENED,
        "payload": {
            "pr_number": 42,
            "title": "Add new feature",
            "author": "developer"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


# ============================================================================
# TEST: WAKE FOR ISSUE COMMENTS (ESCALATION RESPONSES)
# ============================================================================

def test_wake_for_escalation_approve(wowvision_agent):
    """Test wakes for escalation APPROVE response"""
    event = {
        "event_type": EVENT_ISSUE_COMMENT,
        "payload": {
            "issue_number": 10,
            "comment_body": "APPROVE: This is acceptable"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_wake_for_escalation_reject(wowvision_agent):
    """Test wakes for escalation REJECT response"""
    event = {
        "event_type": EVENT_ISSUE_COMMENT,
        "payload": {
            "issue_number": 11,
            "comment_body": "REJECT: Not acceptable"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_wake_for_vision_violation_comment(wowvision_agent):
    """Test wakes for vision-violation labeled issue"""
    event = {
        "event_type": EVENT_ISSUE_COMMENT,
        "payload": {
            "issue_number": 12,
            "comment_body": "This is a vision-violation issue"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_skip_regular_issue_comment(wowvision_agent):
    """Test skips regular issue comments"""
    event = {
        "event_type": EVENT_ISSUE_COMMENT,
        "payload": {
            "issue_number": 13,
            "comment_body": "Great work on this feature!"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: WAKE FOR COMMITS (EXCEPT BOTS)
# ============================================================================

def test_wake_for_human_commit(wowvision_agent):
    """Test wakes for human commit"""
    event = {
        "event_type": EVENT_COMMIT_PUSHED,
        "payload": {
            "commit_sha": "abc123def456",
            "author": "developer@example.com"
        }
    }
    
    assert wowvision_agent.should_wake(event) is True


def test_skip_bot_commit(wowvision_agent):
    """Test skips bot commits"""
    event = {
        "event_type": EVENT_COMMIT_PUSHED,
        "payload": {
            "commit_sha": "bot789",
            "author": "github-actions[bot]"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_dependabot_commit(wowvision_agent):
    """Test skips dependabot commits"""
    event = {
        "event_type": EVENT_COMMIT_PUSHED,
        "payload": {
            "commit_sha": "dep123",
            "author": "dependabot[bot]"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_renovate_commit(wowvision_agent):
    """Test skips renovate commits"""
    event = {
        "event_type": EVENT_COMMIT_PUSHED,
        "payload": {
            "commit_sha": "ren456",
            "author": "renovate[bot]"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: SKIP FILE DELETIONS
# ============================================================================

def test_skip_file_deletion(wowvision_agent):
    """Test skips file deletions"""
    event = {
        "event_type": EVENT_FILE_DELETED,
        "payload": {
            "file_path": "old_file.py"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: SKIP PR CLOSED
# ============================================================================

def test_skip_pr_closed(wowvision_agent):
    """Test skips PR closed"""
    event = {
        "event_type": EVENT_PR_CLOSED,
        "payload": {
            "pr_number": 99
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: SKIP UNKNOWN EVENTS
# ============================================================================

def test_skip_unknown_event_type(wowvision_agent):
    """Test skips unknown event types"""
    event = {
        "event_type": "custom.unknown.event",
        "payload": {}
    }
    
    assert wowvision_agent.should_wake(event) is False


def test_skip_branch_events(wowvision_agent):
    """Test skips branch creation/deletion"""
    event = {
        "event_type": "github.branch.created",
        "payload": {
            "branch_name": "feature/new-branch"
        }
    }
    
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_wake_with_empty_payload(wowvision_agent):
    """Test handles empty payload gracefully"""
    event = {
        "event_type": EVENT_FILE_CREATED,
        "payload": {}
    }
    
    # Should not crash, defaults to wake
    result = wowvision_agent.should_wake(event)
    assert isinstance(result, bool)


def test_wake_with_missing_event_type(wowvision_agent):
    """Test handles missing event_type gracefully"""
    event = {
        "payload": {
            "file_path": "test.py"
        }
    }
    
    # Should not crash, defaults to skip
    assert wowvision_agent.should_wake(event) is False


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 1.2 Test Coverage:

✅ Wake for file creations (Python, HTML, MD docs)
✅ Skip README.md (root and subdirectories)
✅ Skip config files (.yaml, .json, .toml, .env)
✅ Skip lock files (package-lock, poetry.lock)
✅ Wake for file updates (same rules as creation)
✅ Wake for PR opened
✅ Wake for issue comments (APPROVE, REJECT, vision-violation)
✅ Skip regular issue comments
✅ Wake for human commits
✅ Skip bot commits (github-actions, dependabot, renovate)
✅ Skip file deletions
✅ Skip PR closed
✅ Skip unknown events
✅ Edge cases (empty payload, missing event_type)

Total: 28 test scenarios (target: 10+) ✅
"""
