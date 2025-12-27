"""
Tests for Epic 4: Learning & Improvement

Story 4.1: process_escalation() - Parse human feedback from GitHub issues
Story 4.2: learn_from_outcome() - Update knowledge base with learnings
Story 4.3: Similarity search - Find and reuse similar past decisions
Story 4.4: End-to-end learning test

Coverage: Unit tests for escalation processing, learning, and similarity search
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any, List

# Import agent classes
from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.agents.base_agent import Decision


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database connection"""
    db = Mock()
    cursor = Mock()
    
    # Setup cursor mock
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    db.cursor.return_value = cursor
    
    return db


@pytest.fixture
def mock_github_client():
    """Mock GitHub client"""
    client = Mock()
    
    # Mock issue
    mock_issue = Mock()
    mock_issue.number = 123
    mock_issue.html_url = "https://github.com/dlai-sd/WAOOAW/issues/123"
    mock_issue.state = "open"
    
    # Mock comment with APPROVE decision
    mock_comment = Mock()
    mock_comment.body = "APPROVE: This file is needed for the new feature"
    mock_comment.user.login = "dlai-sd"
    mock_comment.created_at = datetime.now()
    
    mock_issue.get_comments.return_value = [mock_comment]
    
    client.get_issue.return_value = mock_issue
    client.comment_on_issue.return_value = None
    
    return client


@pytest.fixture
def wowvision_agent(mock_db, mock_github_client):
    """Create WowVision Prime agent with mocks"""
    config = {
        "agent_id": "WowVision-Prime",
        "github_repo": "dlai-sd/WAOOAW",
        "github_token": "fake_token_for_testing",
        "database_url": "postgresql://test:test@localhost/test",
        "anthropic_api_key": "fake_anthropic_key",
    }
    
    # Mock all initialization methods to prevent actual connections
    with patch('waooaw.agents.base_agent.WAAOOWAgent._init_github'), \
         patch('waooaw.agents.base_agent.WAAOOWAgent._init_database', return_value=mock_db), \
         patch('waooaw.agents.base_agent.WAAOOWAgent._init_vector_memory'), \
         patch('waooaw.agents.base_agent.WAAOOWAgent._init_llm'), \
         patch('waooaw.vision.vision_stack.VisionStack'):
        
        agent = WowVisionPrime(config)
        agent.db = mock_db
        agent.github_client = mock_github_client
        
        return agent


# ============================================================================
# STORY 4.1: process_escalation() TESTS
# ============================================================================

class TestStory41ProcessEscalation:
    """Tests for Story 4.1: Process escalation and parse human feedback"""
    
    def test_process_escalation_approve(self, wowvision_agent, mock_github_client):
        """Test processing APPROVE decision from human"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 1,
                "issue_number": 123,
                "agent_id": "WowVision-Prime",
                "reason": "Python file created in Phase 1"
            }
        }
        
        # Mock comment with APPROVE
        mock_comment = Mock()
        mock_comment.body = "APPROVE: This is a configuration file, not executable code"
        mock_comment.user.login = "dlai-sd"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify issue was fetched
        mock_github_client.get_issue.assert_called_once_with(123)
        
        # Verify database was updated
        cursor = wowvision_agent.db.cursor.return_value
        assert cursor.execute.called
        
        # Check UPDATE query was called with correct status
        update_call = [call for call in cursor.execute.call_args_list 
                      if 'UPDATE human_escalations' in str(call)]
        assert len(update_call) > 0
        
        # Verify acknowledgment comment was posted
        assert mock_github_client.comment_on_issue.called
        comment_text = mock_github_client.comment_on_issue.call_args[1]['comment']
        assert "APPROVED" in comment_text
        assert "dlai-sd" in comment_text
        
        # Verify issue was closed
        assert mock_issue.edit.called
        assert mock_issue.edit.call_args[1]['state'] == 'closed'
    
    def test_process_escalation_reject(self, wowvision_agent, mock_github_client):
        """Test processing REJECT decision from human"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 2,
                "issue_number": 124,
                "agent_id": "WowVision-Prime",
                "reason": "Unauthorized API endpoint"
            }
        }
        
        # Mock comment with REJECT
        mock_comment = Mock()
        mock_comment.body = "REJECT: This violates our security policy"
        mock_comment.user.login = "security-team"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify acknowledgment contains REJECTED
        comment_text = mock_github_client.comment_on_issue.call_args[1]['comment']
        assert "REJECTED" in comment_text
        assert "security-team" in comment_text
        
        # Verify issue was closed
        mock_issue.edit.assert_called_once()
        assert mock_issue.edit.call_args[1]['state'] == 'closed'
    
    def test_process_escalation_modify(self, wowvision_agent, mock_github_client):
        """Test processing MODIFY decision from human"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 3,
                "issue_number": 125,
                "agent_id": "WowVision-Prime",
                "reason": "Missing documentation"
            }
        }
        
        # Mock comment with MODIFY
        mock_comment = Mock()
        mock_comment.body = "MODIFY: Add docstrings and type hints"
        mock_comment.user.login = "lead-dev"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify acknowledgment contains MODIFICATION REQUESTED
        comment_text = mock_github_client.comment_on_issue.call_args[1]['comment']
        assert "MODIFICATION REQUESTED" in comment_text
        assert "Add docstrings and type hints" in comment_text
    
    def test_process_escalation_no_decision_yet(self, wowvision_agent, mock_github_client, caplog):
        """Test processing escalation when no decision comment exists yet"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 4,
                "issue_number": 126,
                "agent_id": "WowVision-Prime",
                "reason": "Unclear violation"
            }
        }
        
        # Mock issue with no decision comments
        mock_comment = Mock()
        mock_comment.body = "I'm investigating this..."
        mock_comment.user.login = "reviewer"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify warning was logged
        assert "No decision found" in caplog.text
        
        # Verify issue was NOT closed
        assert not mock_issue.edit.called
    
    def test_process_escalation_multiple_comments(self, wowvision_agent, mock_github_client):
        """Test processing escalation with multiple comments (first decision wins)"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 5,
                "issue_number": 127,
                "agent_id": "WowVision-Prime",
                "reason": "Test violation"
            }
        }
        
        # Mock multiple comments
        comment1 = Mock()
        comment1.body = "Let me think about this..."
        comment1.user.login = "reviewer1"
        comment1.created_at = datetime.now() - timedelta(hours=2)
        
        comment2 = Mock()
        comment2.body = "APPROVE: Makes sense after review"
        comment2.user.login = "reviewer2"
        comment2.created_at = datetime.now() - timedelta(hours=1)
        
        comment3 = Mock()
        comment3.body = "REJECT: Wait, I changed my mind"  # This should be ignored
        comment3.user.login = "reviewer2"
        comment3.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [comment1, comment2, comment3]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify first decision (APPROVE) was used
        comment_text = mock_github_client.comment_on_issue.call_args[1]['comment']
        assert "APPROVED" in comment_text
        assert "reviewer2" in comment_text
    
    def test_process_escalation_case_insensitive(self, wowvision_agent, mock_github_client):
        """Test that decision keywords are case-insensitive"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 6,
                "issue_number": 128,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
            }
        }
        
        # Mock comment with lowercase decision
        mock_comment = Mock()
        mock_comment.body = "approve: looks good to me"
        mock_comment.user.login = "reviewer"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify decision was recognized
        comment_text = mock_github_client.comment_on_issue.call_args[1]['comment']
        assert "APPROVED" in comment_text
    
    def test_process_escalation_missing_issue_number(self, wowvision_agent, caplog):
        """Test error handling when issue number is missing"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 7,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
                # No issue_number
            }
        }
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify error was logged
        assert "No issue number" in caplog.text
    
    def test_process_escalation_github_api_error(self, wowvision_agent, mock_github_client, caplog):
        """Test error handling when GitHub API fails"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 8,
                "issue_number": 129,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
            }
        }
        
        # Mock GitHub API error
        mock_github_client.get_issue.side_effect = Exception("API Error")
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify error was logged (but agent continues)
        assert "Failed to process escalation" in caplog.text


# ============================================================================
# HELPER METHODS TESTS
# ============================================================================

class TestEscalationHelpers:
    """Tests for escalation helper methods"""
    
    def test_update_escalation_status(self, wowvision_agent):
        """Test updating escalation status in database"""
        # Setup
        escalation_id = 1
        status = "resolved"
        resolution_data = {
            "decision": "approved",
            "reasoning": "Valid exception",
            "decided_by": "dlai-sd",
            "decided_at": datetime.now().isoformat()
        }
        
        # Execute
        wowvision_agent._update_escalation_status(
            escalation_id=escalation_id,
            status=status,
            resolution_data=resolution_data
        )
        
        # Verify UPDATE query was executed
        cursor = wowvision_agent.db.cursor.return_value
        assert cursor.execute.called
        
        # Verify SQL contains UPDATE and correct fields
        sql_call = cursor.execute.call_args[0][0]
        assert "UPDATE human_escalations" in sql_call
        assert "status = %s" in sql_call
        assert "resolution_data = %s" in sql_call
        assert "resolved_at = NOW()" in sql_call
        
        # Verify parameters
        params = cursor.execute.call_args[0][1]
        assert params[0] == status
        assert params[2] == escalation_id
        
        # Verify commit was called
        assert wowvision_agent.db.commit.called
    
    def test_format_acknowledgment_comment_approve(self, wowvision_agent):
        """Test formatting acknowledgment comment for APPROVE"""
        # Execute
        comment = wowvision_agent._format_acknowledgment_comment(
            human_decision="approved",
            human_reasoning="This is a valid configuration file",
            decided_by="dlai-sd"
        )
        
        # Verify format
        assert "✅" in comment
        assert "APPROVED" in comment
        assert "@dlai-sd" in comment
        assert "This is a valid configuration file" in comment
        assert "update my validation rules" in comment
        assert "WowVision Prime" in comment
    
    def test_format_acknowledgment_comment_reject(self, wowvision_agent):
        """Test formatting acknowledgment comment for REJECT"""
        # Execute
        comment = wowvision_agent._format_acknowledgment_comment(
            human_decision="rejected",
            human_reasoning="Violates security policy",
            decided_by="security-team"
        )
        
        # Verify format
        assert "❌" in comment
        assert "REJECTED" in comment
        assert "@security-team" in comment
        assert "Violates security policy" in comment
        assert "enforce this rule more strictly" in comment
    
    def test_format_acknowledgment_comment_modify(self, wowvision_agent):
        """Test formatting acknowledgment comment for MODIFY"""
        # Execute
        comment = wowvision_agent._format_acknowledgment_comment(
            human_decision="modify",
            human_reasoning="Add documentation",
            decided_by="lead-dev"
        )
        
        # Verify format
        assert "🔧" in comment
        assert "MODIFICATION REQUESTED" in comment
        assert "@lead-dev" in comment
        assert "Add documentation" in comment
        assert "track this case" in comment


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestStory41Integration:
    """Integration tests for Story 4.1"""
    
    def test_end_to_end_escalation_flow(self, wowvision_agent, mock_github_client):
        """Test complete escalation flow from creation to resolution"""
        # 1. Create violation and escalate
        filename = "app/test.py"
        commit = {
            "sha": "abc123",
            "author": "developer",
            "message": "Add test file"
        }
        decision = Decision(
            approved=False,
            reason="Python file in Phase 1",
            confidence=0.95,
            method="deterministic",
            citations=["Layer 1: No Python in Phase 1"]
        )
        
        # Mock issue creation
        mock_issue = Mock()
        mock_issue.number = 150
        mock_github_client.create_issue.return_value = mock_issue
        
        # Create escalation
        issue_number = wowvision_agent._escalate_violation(filename, commit, decision)
        assert issue_number == 150
        
        # 2. Simulate human response
        mock_comment = Mock()
        mock_comment.body = "APPROVE: This is actually a test fixture, not executable code"
        mock_comment.user.login = "dlai-sd"
        mock_comment.created_at = datetime.now()
        
        mock_issue_retrieved = mock_github_client.get_issue.return_value
        mock_issue_retrieved.get_comments.return_value = [mock_comment]
        
        # 3. Process escalation
        escalation_data = {
            "escalation": {
                "id": 1,
                "issue_number": 150,
                "agent_id": "WowVision-Prime",
                "reason": "Python file in Phase 1"
            }
        }
        
        wowvision_agent._process_escalation(escalation_data)
        
        # 4. Verify complete flow
        # - Issue was created
        assert mock_github_client.create_issue.called
        
        # - Escalation was logged
        cursor = wowvision_agent.db.cursor.return_value
        insert_calls = [call for call in cursor.execute.call_args_list 
                       if 'INSERT INTO human_escalations' in str(call)]
        assert len(insert_calls) > 0
        
        # - Issue was fetched
        mock_github_client.get_issue.assert_called_with(150)
        
        # - Status was updated
        update_calls = [call for call in cursor.execute.call_args_list 
                       if 'UPDATE human_escalations' in str(call)]
        assert len(update_calls) > 0
        
        # - Acknowledgment was posted
        assert mock_github_client.comment_on_issue.called
        
        # - Issue was closed
        assert mock_issue_retrieved.edit.called


# ============================================================================
# ACCEPTANCE CRITERIA TESTS
# ============================================================================

class TestStory41AcceptanceCriteria:
    """Test acceptance criteria for Story 4.1"""
    
    def test_ac1_escalations_fetched_correctly(self, wowvision_agent, mock_github_client):
        """AC: Escalations fetched correctly from GitHub"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 1,
                "issue_number": 200,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
            }
        }
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify
        mock_github_client.get_issue.assert_called_once_with(200)
    
    def test_ac2_comments_parsed_accurately(self, wowvision_agent, mock_github_client):
        """AC: Comments parsed accurately for APPROVE/REJECT/MODIFY"""
        test_cases = [
            ("APPROVE: Good", "approved"),
            ("REJECT: Bad", "rejected"),
            ("MODIFY: Change this", "modify"),
            ("approve: lowercase works", "approved"),
            ("Reject: Capitalized works", "rejected"),
        ]
        
        for i, (comment_body, expected_decision) in enumerate(test_cases):
            # Setup - create fresh escalation data for each test case
            escalation_data = {
                "escalation": {
                    "id": i + 1,  # Unique ID for each test
                    "issue_number": 201 + i,  # Unique issue number
                    "agent_id": "WowVision-Prime",
                    "reason": f"Test case {i}"
                }
            }
            
            # Create fresh mock comment for this test case
            mock_comment = Mock()
            mock_comment.body = comment_body
            mock_comment.user.login = "tester"
            mock_comment.created_at = datetime(2025, 12, 27, 10, 0, 0)  # Fixed datetime
            
            # Create fresh mock issue for this test case
            mock_issue = Mock()
            mock_issue.number = 201 + i
            mock_issue.html_url = f"https://github.com/test/repo/issues/{201 + i}"
            mock_issue.get_comments.return_value = [mock_comment]
            mock_issue.edit = Mock()
            
            # Configure get_issue to return our mock issue
            mock_github_client.get_issue.return_value = mock_issue
            
            # Reset cursor mock for each iteration
            cursor = wowvision_agent.db.cursor.return_value
            cursor.execute.reset_mock()
            
            # Execute
            wowvision_agent._process_escalation(escalation_data)
            
            # Verify decision was parsed correctly
            # Find the UPDATE call and check resolution_data
            found = False
            for call_args in cursor.execute.call_args_list:
                sql = call_args[0][0]
                if "UPDATE human_escalations" in sql:
                    params = call_args[0][1]
                    resolution_json = params[1]
                    resolution_data = json.loads(resolution_json)
                    assert resolution_data["decision"] == expected_decision, \
                        f"Test case '{comment_body}' failed: expected {expected_decision}, got {resolution_data['decision']}"
                    found = True
                    break
            
            assert found, f"No UPDATE query found for test case '{comment_body}'"
    
    def test_ac3_human_decision_extracted(self, wowvision_agent, mock_github_client):
        """AC: Human decision and reasoning extracted correctly"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 1,
                "issue_number": 202,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
            }
        }
        
        expected_reasoning = "This is the detailed reasoning for my decision"
        
        mock_comment = Mock()
        mock_comment.body = f"APPROVE: {expected_reasoning}"
        mock_comment.user.login = "decision-maker"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify reasoning was extracted and stored
        cursor = wowvision_agent.db.cursor.return_value
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "UPDATE human_escalations" in sql:
                params = call_args[0][1]
                resolution_json = params[1]
                resolution_data = json.loads(resolution_json)
                assert resolution_data["reasoning"] == expected_reasoning
                assert resolution_data["decided_by"] == "decision-maker"
                break
    
    def test_ac4_status_updated_pending_to_resolved(self, wowvision_agent, mock_github_client):
        """AC: Status updated from 'pending' to 'resolved'"""
        # Setup
        escalation_data = {
            "escalation": {
                "id": 42,
                "issue_number": 203,
                "agent_id": "WowVision-Prime",
                "reason": "Test"
            }
        }
        
        mock_comment = Mock()
        mock_comment.body = "APPROVE: All good"
        mock_comment.user.login = "approver"
        mock_comment.created_at = datetime.now()
        
        mock_issue = mock_github_client.get_issue.return_value
        mock_issue.get_comments.return_value = [mock_comment]
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify status updated to 'resolved'
        cursor = wowvision_agent.db.cursor.return_value
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "UPDATE human_escalations" in sql:
                params = call_args[0][1]
                assert params[0] == "resolved"  # status parameter
                assert params[2] == 42  # escalation_id parameter
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
