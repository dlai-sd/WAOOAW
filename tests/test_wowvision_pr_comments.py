"""
Unit tests for Story 2.3: WowVision PR Comment Implementation

Tests the _comment_on_pr() method in WowVisionPrime:
- Approval comment formatting
- Rejection comment formatting  
- Violation details inclusion
- Issue linking
- GitHub client integration
- Error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import logging

from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.agents.base_agent import Decision

# Setup logger for tests
logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = MagicMock()
    cursor = MagicMock()
    db.cursor.return_value = cursor
    return db


@pytest.fixture
def mock_github_client():
    """Mock GitHub client"""
    client = MagicMock()
    return client


@pytest.fixture
def wowvision_agent(mock_github_client, mock_db):
    """WowVisionPrime instance with mocked dependencies"""
    agent = WowVisionPrime.__new__(WowVisionPrime)
    
    # Set required attributes
    agent.agent_id = "WowVision-Prime"
    agent.db = mock_db
    agent.logger = logger
    agent.github_client = mock_github_client
    agent.vision_stack = None
    agent.core_identity = {}
    agent.policies = {}
    agent.current_phase = "phase1_foundation"
    
    return agent


@pytest.fixture
def approval_decision():
    """Sample approval decision"""
    return Decision(
        approved=True,
        reason="All files comply with WAOOAW vision principles",
        confidence=0.98,
        method="deterministic",
        citations=["vision.yaml:naming_conventions", "policies.yaml:python_style"],
        metadata={"decision_id": "dec_approve_123"}
    )


@pytest.fixture
def rejection_decision():
    """Sample rejection decision"""
    return Decision(
        approved=False,
        reason="Files violate naming conventions",
        confidence=0.95,
        method="deterministic",
        citations=["vision.yaml:naming_conventions"],
        metadata={"decision_id": "dec_reject_456"}
    )


@pytest.fixture
def sample_violations():
    """Sample violation list"""
    return [
        {
            "filename": "src/badFile.py",
            "reason": "Must use snake_case naming"
        },
        {
            "filename": "lib/WrongName.py",
            "reason": "Python files must use snake_case"
        }
    ]


# ============================================================================
# TEST: APPROVAL COMMENTS
# ============================================================================

def test_approval_comment_format(wowvision_agent, mock_github_client, approval_decision):
    """Test approval comment has correct format"""
    pr_number = 42
    
    result = wowvision_agent._comment_on_pr(pr_number, approval_decision)
    
    # Verify success
    assert result is True
    
    # Verify GitHub client called
    mock_github_client.comment_on_pr.assert_called_once()
    call_args = mock_github_client.comment_on_pr.call_args
    
    # Verify PR number
    assert call_args[1]['pr_number'] == pr_number
    
    # Verify comment content
    comment = call_args[1]['comment']
    assert "✅" in comment
    assert "APPROVED" in comment
    assert "All files comply" in comment or approval_decision.reason in comment
    assert f"{approval_decision.confidence:.2%}" in comment
    assert approval_decision.method in comment
    assert "WowVision Prime" in comment


def test_approval_comment_includes_decision_summary(wowvision_agent, mock_github_client, approval_decision):
    """Test approval comment includes all decision details"""
    pr_number = 10
    
    wowvision_agent._comment_on_pr(pr_number, approval_decision)
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Check decision summary fields
    assert "Status" in comment and "Approved" in comment
    assert "Confidence" in comment
    assert "Method" in comment
    assert "Reason" in comment


# ============================================================================
# TEST: REJECTION COMMENTS
# ============================================================================

def test_rejection_comment_format(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment has correct format"""
    pr_number = 43
    
    result = wowvision_agent._comment_on_pr(pr_number, rejection_decision)
    
    # Verify success
    assert result is True
    
    # Verify GitHub client called
    mock_github_client.comment_on_pr.assert_called_once()
    call_args = mock_github_client.comment_on_pr.call_args
    
    # Verify comment content
    comment = call_args[1]['comment']
    assert "❌" in comment
    assert "REJECTED" in comment
    assert "violation" in comment.lower()
    assert f"{rejection_decision.confidence:.2%}" in comment
    assert rejection_decision.method in comment
    assert rejection_decision.reason in comment


def test_rejection_with_issue_link(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment includes issue link"""
    pr_number = 44
    issue_number = 99
    
    wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        issue_number=issue_number
    )
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Check for issue link
    assert f"#{issue_number}" in comment
    assert "issue" in comment.lower()


def test_rejection_with_single_violation(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment with single violation"""
    pr_number = 45
    violations = [{"filename": "test.py", "reason": "Invalid name"}]
    
    wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        violations=violations
    )
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Check violation count (singular)
    assert "1 violation" in comment
    assert "test.py" in comment
    assert "Invalid name" in comment


def test_rejection_with_multiple_violations(wowvision_agent, mock_github_client, rejection_decision, sample_violations):
    """Test rejection comment with multiple violations"""
    pr_number = 46
    
    wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        violations=sample_violations
    )
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Check violation count (plural)
    assert "2 violations" in comment
    
    # Check both violations listed
    assert "badFile.py" in comment
    assert "WrongName.py" in comment
    assert "snake_case" in comment


def test_rejection_includes_next_steps(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment includes actionable next steps"""
    pr_number = 47
    
    wowvision_agent._comment_on_pr(pr_number, rejection_decision)
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Check for next steps section
    assert "Next Steps" in comment
    assert "Review" in comment or "Update" in comment


# ============================================================================
# TEST: GITHUB CLIENT INTEGRATION
# ============================================================================

def test_comment_calls_github_client(wowvision_agent, mock_github_client, approval_decision):
    """Test _comment_on_pr calls GitHub client with correct parameters"""
    pr_number = 50
    
    result = wowvision_agent._comment_on_pr(pr_number, approval_decision)
    
    # Verify GitHub client called once
    assert mock_github_client.comment_on_pr.called
    assert mock_github_client.comment_on_pr.call_count == 1
    
    # Verify return value
    assert result is True


def test_comment_returns_false_when_github_unavailable(wowvision_agent, approval_decision):
    """Test _comment_on_pr returns False when GitHub client unavailable"""
    wowvision_agent.github_client = None
    
    result = wowvision_agent._comment_on_pr(42, approval_decision)
    
    assert result is False


def test_comment_handles_github_api_errors(wowvision_agent, mock_github_client, approval_decision):
    """Test _comment_on_pr handles GitHub API errors gracefully"""
    from github import GithubException
    
    mock_github_client.comment_on_pr.side_effect = GithubException(
        status=404,
        data={"message": "PR not found"},
        headers={}
    )
    
    result = wowvision_agent._comment_on_pr(999, approval_decision)
    
    # Should return False on error
    assert result is False


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_comment_with_no_violations_list(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment without violations list"""
    pr_number = 51
    
    result = wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        violations=None
    )
    
    assert result is True
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Should still mention violation in singular form
    assert "1 violation" in comment


def test_comment_with_empty_violations_list(wowvision_agent, mock_github_client, rejection_decision):
    """Test rejection comment with empty violations list"""
    pr_number = 52
    
    result = wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        violations=[]
    )
    
    assert result is True


def test_comment_formats_confidence_percentage(wowvision_agent, mock_github_client):
    """Test confidence is formatted as percentage"""
    decision = Decision(
        approved=True,
        reason="Test",
        confidence=0.8547,  # Should format as 85.47%
        method="test"
    )
    
    wowvision_agent._comment_on_pr(42, decision)
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    assert "85.47%" in comment


# ============================================================================
# TEST: END-TO-END SCENARIOS
# ============================================================================

def test_full_approval_flow(wowvision_agent, mock_github_client, approval_decision):
    """Test complete approval comment flow"""
    pr_number = 100
    
    # Post approval comment
    result = wowvision_agent._comment_on_pr(pr_number, approval_decision)
    
    # Verify success
    assert result is True
    
    # Verify comment structure
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Must have approval indicator
    assert "✅" in comment
    
    # Must have decision details
    assert "98.00%" in comment  # confidence
    assert "deterministic" in comment  # method
    
    # Must be positive tone
    assert "approved" in comment.lower() or "passed" in comment.lower()


def test_full_rejection_flow_with_all_details(
    wowvision_agent, mock_github_client, rejection_decision, sample_violations
):
    """Test complete rejection comment flow with all optional parameters"""
    pr_number = 101
    issue_number = 202
    
    # Post rejection comment with violations and issue
    result = wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=rejection_decision,
        violations=sample_violations,
        issue_number=issue_number
    )
    
    # Verify success
    assert result is True
    
    # Verify comment structure
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Must have rejection indicator
    assert "❌" in comment
    
    # Must have decision details
    assert "95.00%" in comment  # confidence
    assert "deterministic" in comment  # method
    assert rejection_decision.reason in comment
    
    # Must have issue link
    assert f"#{issue_number}" in comment
    
    # Must have violations
    assert "2 violations" in comment
    assert "badFile.py" in comment
    assert "WrongName.py" in comment
    
    # Must have next steps
    assert "Next Steps" in comment


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 2.3 Test Coverage:

✅ Approval comments (2 tests)
✅ Rejection comments (5 tests)
✅ GitHub client integration (3 tests)
✅ Edge cases (3 tests)
✅ End-to-end scenarios (2 tests)

Total: 15 unit tests ✅

All _comment_on_pr() functionality tested with mocked GitHub client.
"""
