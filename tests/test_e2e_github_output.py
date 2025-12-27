"""
End-to-End Integration Tests for Story 2.5: WowVision GitHub Output Flow

Tests the complete workflow from violation detection to GitHub outputs:
- Violation detected → Issue created
- Decision made → PR commented
- Full flow: Violation → Issue + PR comment
- Performance: Latency measurements (<2s for issue, <1s for PR)
- Content validation: All fields populated correctly
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import logging
import time
from datetime import datetime

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
def violation_data():
    """Sample violation data"""
    return {
        "filename": "src/bad_file.py",
        "commit": {
            "sha": "abc123def456789",
            "author": "developer123",
            "message": "Add new feature file"
        },
        "decision": Decision(
            approved=False,
            reason="File violates naming convention: must use snake_case",
            confidence=0.95,
            method="deterministic",
            citations=["vision.yaml:naming_conventions", "policies.yaml:python_style"],
            metadata={"decision_id": "dec_violation_001"}
        )
    }


@pytest.fixture
def approval_data():
    """Sample approval data"""
    return {
        "pr_number": 42,
        "decision": Decision(
            approved=True,
            reason="All files comply with WAOOAW vision principles",
            confidence=0.98,
            method="deterministic",
            citations=["vision.yaml:naming_conventions"],
            metadata={"decision_id": "dec_approval_001"}
        )
    }


# ============================================================================
# TEST: VIOLATION → ISSUE CREATION
# ============================================================================

def test_violation_to_issue_flow(wowvision_agent, mock_github_client, mock_db, violation_data):
    """Test end-to-end flow from violation detection to issue creation"""
    # Setup mock issue
    mock_issue = MagicMock()
    mock_issue.number = 101
    mock_github_client.create_issue.return_value = mock_issue
    
    # Execute violation escalation
    start_time = time.time()
    issue_number = wowvision_agent._escalate_violation(
        filename=violation_data["filename"],
        commit=violation_data["commit"],
        decision=violation_data["decision"]
    )
    elapsed_time = time.time() - start_time
    
    # Verify issue created
    assert issue_number == 101
    assert mock_github_client.create_issue.called
    
    # Verify performance (<2s requirement)
    assert elapsed_time < 2.0, f"Issue creation took {elapsed_time:.3f}s (expected <2s)"
    
    # Verify issue content
    call_args = mock_github_client.create_issue.call_args
    title = call_args[1]['title']
    body = call_args[1]['body']
    labels = call_args[1]['labels']
    
    # Title format
    assert "🚨 Vision Violation:" in title
    assert violation_data["filename"] in title
    
    # Body contains all required fields
    assert violation_data["filename"] in body
    assert violation_data["commit"]["sha"][:7] in body
    assert violation_data["commit"]["author"] in body
    assert violation_data["decision"].reason in body
    assert f"{violation_data['decision'].confidence:.2%}" in body
    assert violation_data["decision"].method in body
    
    # Citations present
    for citation in violation_data["decision"].citations:
        assert citation in body
    
    # Labels correct
    assert "vision-violation" in labels
    assert "agent-escalation" in labels
    
    # Database logging called
    cursor = mock_db.cursor.return_value
    assert cursor.execute.called
    assert mock_db.commit.called


def test_violation_to_issue_with_all_fields_populated(wowvision_agent, mock_github_client, violation_data):
    """Test that issue creation populates ALL required fields"""
    mock_issue = MagicMock()
    mock_issue.number = 102
    mock_github_client.create_issue.return_value = mock_issue
    
    issue_number = wowvision_agent._escalate_violation(
        filename=violation_data["filename"],
        commit=violation_data["commit"],
        decision=violation_data["decision"]
    )
    
    assert issue_number is not None
    
    # Get issue body
    call_args = mock_github_client.create_issue.call_args
    body = call_args[1]['body']
    
    # Verify ALL Story 2.5 required fields present
    required_fields = [
        violation_data["filename"],                     # File
        violation_data["commit"]["sha"][:7],           # Commit (short SHA)
        violation_data["commit"]["author"],             # Author
        violation_data["decision"].reason,              # Violation reason
        f"{violation_data['decision'].confidence:.2%}", # Confidence
        violation_data["decision"].method,              # Method
        violation_data["commit"]["message"],            # Context (commit message)
    ]
    
    for field in required_fields:
        assert field in body, f"Required field missing from issue body: {field}"
    
    # Verify action options present
    assert "APPROVE" in body
    assert "REJECT" in body
    assert "MODIFY" in body


# ============================================================================
# TEST: DECISION → PR COMMENT
# ============================================================================

def test_decision_to_pr_comment_flow(wowvision_agent, mock_github_client, approval_data):
    """Test end-to-end flow from decision to PR comment"""
    # Execute PR comment
    start_time = time.time()
    result = wowvision_agent._comment_on_pr(
        pr_number=approval_data["pr_number"],
        decision=approval_data["decision"]
    )
    elapsed_time = time.time() - start_time
    
    # Verify comment posted
    assert result is True
    assert mock_github_client.comment_on_pr.called
    
    # Verify performance (<1s requirement)
    assert elapsed_time < 1.0, f"PR comment took {elapsed_time:.3f}s (expected <1s)"
    
    # Verify comment content
    call_args = mock_github_client.comment_on_pr.call_args
    pr_number = call_args[1]['pr_number']
    comment = call_args[1]['comment']
    
    # PR number correct
    assert pr_number == 42
    
    # Comment contains all required fields
    assert "✅" in comment  # Approval indicator
    assert "APPROVED" in comment
    assert f"{approval_data['decision'].confidence:.2%}" in comment
    assert approval_data["decision"].method in comment
    assert approval_data["decision"].reason in comment


def test_rejection_to_pr_comment_with_issue_link(wowvision_agent, mock_github_client):
    """Test rejection decision creates PR comment with issue link"""
    rejection_decision = Decision(
        approved=False,
        reason="Files violate naming conventions",
        confidence=0.92,
        method="deterministic",
        metadata={"decision_id": "dec_reject_002"}
    )
    
    violations = [
        {"filename": "src/BadFile.py", "reason": "Must use snake_case"},
        {"filename": "lib/WrongName.py", "reason": "Python files must use snake_case"}
    ]
    
    issue_number = 999
    
    start_time = time.time()
    result = wowvision_agent._comment_on_pr(
        pr_number=50,
        decision=rejection_decision,
        violations=violations,
        issue_number=issue_number
    )
    elapsed_time = time.time() - start_time
    
    # Verify success and performance
    assert result is True
    assert elapsed_time < 1.0
    
    # Verify comment content
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Rejection format
    assert "❌" in comment
    assert "REJECTED" in comment
    assert "2 violations" in comment
    
    # Issue link present
    assert f"#{issue_number}" in comment
    
    # Violations listed
    assert "BadFile.py" in comment
    assert "WrongName.py" in comment
    assert "snake_case" in comment


# ============================================================================
# TEST: FULL END-TO-END FLOW
# ============================================================================

def test_full_e2e_violation_to_outputs(wowvision_agent, mock_github_client, mock_db, violation_data):
    """Test complete flow: Violation detected → Issue created + PR commented"""
    # Setup mocks
    mock_issue = MagicMock()
    mock_issue.number = 200
    mock_github_client.create_issue.return_value = mock_issue
    
    pr_number = 75
    
    # Step 1: Violation detected → Issue created
    start_time_total = time.time()
    
    start_time_issue = time.time()
    issue_number = wowvision_agent._escalate_violation(
        filename=violation_data["filename"],
        commit=violation_data["commit"],
        decision=violation_data["decision"]
    )
    elapsed_issue = time.time() - start_time_issue
    
    assert issue_number == 200
    assert elapsed_issue < 2.0, f"Issue creation took {elapsed_issue:.3f}s (expected <2s)"
    
    # Step 2: Decision made → PR commented with issue link
    start_time_pr = time.time()
    violations = [{
        "filename": violation_data["filename"],
        "reason": violation_data["decision"].reason
    }]
    
    result = wowvision_agent._comment_on_pr(
        pr_number=pr_number,
        decision=violation_data["decision"],
        violations=violations,
        issue_number=issue_number
    )
    elapsed_pr = time.time() - start_time_pr
    
    assert result is True
    assert elapsed_pr < 1.0, f"PR comment took {elapsed_pr:.3f}s (expected <1s)"
    
    # Total flow time
    elapsed_total = time.time() - start_time_total
    assert elapsed_total < 3.0, f"Total E2E flow took {elapsed_total:.3f}s (expected <3s)"
    
    # Verify both outputs created correctly
    assert mock_github_client.create_issue.call_count == 1
    assert mock_github_client.comment_on_pr.call_count == 1
    
    # Verify issue and PR comment are linked
    issue_call = mock_github_client.create_issue.call_args
    pr_call = mock_github_client.comment_on_pr.call_args
    
    issue_body = issue_call[1]['body']
    pr_comment = pr_call[1]['comment']
    
    # Issue has violation details
    assert violation_data["filename"] in issue_body
    assert violation_data["decision"].reason in issue_body
    
    # PR comment references issue
    assert f"#{issue_number}" in pr_comment
    assert violation_data["filename"] in pr_comment


def test_approval_flow_creates_only_pr_comment(wowvision_agent, mock_github_client, approval_data):
    """Test that approval flow only creates PR comment (no issue)"""
    # Execute approval flow
    result = wowvision_agent._comment_on_pr(
        pr_number=approval_data["pr_number"],
        decision=approval_data["decision"]
    )
    
    # Verify only PR comment created (no issue)
    assert result is True
    assert mock_github_client.comment_on_pr.call_count == 1
    assert mock_github_client.create_issue.call_count == 0
    
    # Verify comment content is approval format
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    assert "✅" in comment
    assert "APPROVED" in comment


# ============================================================================
# TEST: PERFORMANCE BENCHMARKS
# ============================================================================

def test_issue_creation_latency_benchmark(wowvision_agent, mock_github_client, violation_data):
    """Benchmark issue creation latency across multiple runs"""
    mock_issue = MagicMock()
    mock_issue.number = 300
    mock_github_client.create_issue.return_value = mock_issue
    
    latencies = []
    num_runs = 10
    
    for _ in range(num_runs):
        start_time = time.time()
        wowvision_agent._escalate_violation(
            filename=violation_data["filename"],
            commit=violation_data["commit"],
            decision=violation_data["decision"]
        )
        elapsed = time.time() - start_time
        latencies.append(elapsed)
    
    # Calculate statistics
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    # All runs should meet <2s requirement
    assert max_latency < 2.0, f"Max latency {max_latency:.3f}s exceeded 2s threshold"
    assert avg_latency < 1.0, f"Average latency {avg_latency:.3f}s should be well under 2s"


def test_pr_comment_latency_benchmark(wowvision_agent, mock_github_client, approval_data):
    """Benchmark PR comment latency across multiple runs"""
    latencies = []
    num_runs = 10
    
    for _ in range(num_runs):
        start_time = time.time()
        wowvision_agent._comment_on_pr(
            pr_number=approval_data["pr_number"],
            decision=approval_data["decision"]
        )
        elapsed = time.time() - start_time
        latencies.append(elapsed)
    
    # Calculate statistics
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    # All runs should meet <1s requirement
    assert max_latency < 1.0, f"Max latency {max_latency:.3f}s exceeded 1s threshold"
    assert avg_latency < 0.5, f"Average latency {avg_latency:.3f}s should be well under 1s"


# ============================================================================
# TEST: CONTENT VALIDATION
# ============================================================================

def test_all_fields_populated_in_issue(wowvision_agent, mock_github_client, violation_data):
    """Validate that ALL required fields are populated in issue"""
    mock_issue = MagicMock()
    mock_issue.number = 400
    mock_github_client.create_issue.return_value = mock_issue
    
    wowvision_agent._escalate_violation(
        filename=violation_data["filename"],
        commit=violation_data["commit"],
        decision=violation_data["decision"]
    )
    
    call_args = mock_github_client.create_issue.call_args
    title = call_args[1]['title']
    body = call_args[1]['body']
    labels = call_args[1]['labels']
    
    # Title
    assert title is not None and len(title) > 0
    assert "🚨" in title
    assert violation_data["filename"] in title
    
    # Body - all required Story 2.5 fields
    required_in_body = [
        violation_data["filename"],                     # File
        violation_data["commit"]["sha"][:7],           # Commit SHA (short)
        violation_data["commit"]["author"],             # Author
        violation_data["decision"].reason,              # Violation reason
        f"{violation_data['decision'].confidence:.2%}", # Confidence
        violation_data["decision"].method,              # Method
        "APPROVE",                                      # Action option 1
        "REJECT",                                       # Action option 2
        "MODIFY",                                       # Action option 3
        "WowVision Prime",                             # Agent attribution
    ]
    
    for field in required_in_body:
        assert field in body, f"Required field '{field}' missing from issue body"
    
    # Labels
    assert len(labels) == 2
    assert "vision-violation" in labels
    assert "agent-escalation" in labels


def test_all_fields_populated_in_pr_comment(wowvision_agent, mock_github_client, approval_data):
    """Validate that ALL required fields are populated in PR comment"""
    wowvision_agent._comment_on_pr(
        pr_number=approval_data["pr_number"],
        decision=approval_data["decision"]
    )
    
    call_args = mock_github_client.comment_on_pr.call_args
    comment = call_args[1]['comment']
    
    # Required fields in PR comment
    required_in_comment = [
        "✅",  # Status indicator
        "APPROVED",  # Status text
        f"{approval_data['decision'].confidence:.2%}",  # Confidence
        approval_data["decision"].method,               # Method
        approval_data["decision"].reason,               # Reason
        "WowVision Prime",                              # Agent attribution
    ]
    
    for field in required_in_comment:
        assert field in comment, f"Required field '{field}' missing from PR comment"


# ============================================================================
# TEST: ERROR HANDLING IN E2E FLOW
# ============================================================================

def test_e2e_flow_handles_github_errors_gracefully(wowvision_agent, mock_github_client, violation_data):
    """Test that E2E flow handles GitHub API errors without crashing"""
    from github import GithubException
    
    # Simulate GitHub API error
    mock_github_client.create_issue.side_effect = GithubException(
        status=503,
        data={"message": "Service unavailable"},
        headers={}
    )
    
    # Should return None but not crash
    issue_number = wowvision_agent._escalate_violation(
        filename=violation_data["filename"],
        commit=violation_data["commit"],
        decision=violation_data["decision"]
    )
    
    assert issue_number is None
    
    # Agent should still be functional for PR comment
    mock_github_client.comment_on_pr.side_effect = None  # Reset
    result = wowvision_agent._comment_on_pr(
        pr_number=42,
        decision=violation_data["decision"]
    )
    
    assert result is True


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 2.5 E2E Test Coverage:

✅ Violation → Issue flow (2 tests)
✅ Decision → PR comment flow (2 tests)
✅ Full E2E flow (2 tests)
✅ Performance benchmarks (2 tests)
✅ Content validation (2 tests)
✅ Error handling (1 test)

Total: 11 integration tests ✅

Validates complete GitHub output workflow with performance and content requirements.
"""
