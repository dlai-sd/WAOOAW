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


# ============================================================================
# STORY 4.2: learn_from_outcome() TESTS
# ============================================================================

class TestStory42LearnFromOutcome:
    """Tests for Story 4.2: Learn from outcomes and update knowledge base"""
    
    def test_learn_from_approved_outcome(self, wowvision_agent):
        """Test learning from APPROVED human decision"""
        # Setup
        decision = Decision(
            approved=False,
            reason="Python file in Phase 1",
            confidence=0.85,
            method="llm",
            citations=["Layer 1: No Python in Phase 1"]
        )
        
        feedback = {
            "reasoning": "This is a test fixture, not executable code",
            "decided_by": "dlai-sd",
            "file_path": "tests/fixtures/sample.py",
            "violation_type": "python_in_phase1"
        }
        
        # Execute
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Verify INSERT was called
        cursor = wowvision_agent.db.cursor.return_value
        assert cursor.execute.called
        
        # Find INSERT call
        insert_found = False
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "INSERT INTO knowledge_base" in sql:
                params = call_args[0][1]
                category = params[0]
                title = params[1]
                content_json = params[2]
                confidence = params[3]
                source = params[4]
                
                # Verify parameters
                assert category == "WowVision-Prime-learnings"
                assert "Allow" in title
                assert "python_in_phase1" in title
                
                # Parse content
                content = json.loads(content_json)
                assert content['outcome'] == 'approved'
                assert content['violation_type'] == 'python_in_phase1'
                assert content['learned_from'] == 'dlai-sd'
                
                # Verify confidence (should be 0.7 for approved)
                assert 0.6 <= confidence <= 0.8
                
                insert_found = True
                break
        
        assert insert_found, "INSERT INTO knowledge_base not found"
        assert wowvision_agent.db.commit.called
    
    def test_learn_from_rejected_outcome(self, wowvision_agent):
        """Test learning from REJECTED human decision"""
        # Setup
        decision = Decision(
            approved=False,
            reason="Unauthorized API endpoint",
            confidence=0.75,
            method="llm"
        )
        
        feedback = {
            "reasoning": "This violates our security policy",
            "decided_by": "security-team",
            "file_path": "app/api/dangerous.py",
            "violation_type": "security_violation"
        }
        
        # Execute
        wowvision_agent.learn_from_outcome(decision, "rejected", feedback)
        
        # Verify learning was stored
        cursor = wowvision_agent.db.cursor.return_value
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "INSERT INTO knowledge_base" in sql:
                params = call_args[0][1]
                title = params[1]
                content_json = params[2]
                confidence = params[3]
                
                # Verify rejection learning
                assert "Reject" in title
                content = json.loads(content_json)
                assert content['outcome'] == 'rejected'
                
                # Rejected outcomes should have higher initial confidence (0.8)
                assert 0.7 <= confidence <= 0.9
                break
    
    def test_learn_updates_existing_pattern(self, wowvision_agent):
        """Test that learning updates existing similar patterns"""
        # Setup - Mock finding an existing pattern
        cursor = wowvision_agent.db.cursor.return_value
        
        # Mock existing pattern
        existing_pattern = {
            "id": 1,
            "title": "Allow python_in_phase1",
            "content": {
                "violation_type": "python_in_phase1",
                "outcome": "approved",
                "rule": {"condition": "Test files", "action": "approved"}
            },
            "confidence": 0.7
        }
        
        # Configure cursor to return existing pattern on SELECT
        cursor.fetchone.return_value = (
            existing_pattern['id'],
            existing_pattern['title'],
            json.dumps(existing_pattern['content']),
            existing_pattern['confidence']
        )
        
        decision = Decision(
            approved=False,
            reason="Python file in Phase 1",
            confidence=0.85,
            method="llm"
        )
        
        feedback = {
            "reasoning": "Another test file",
            "decided_by": "developer",
            "file_path": "tests/test_new.py",
            "violation_type": "python_in_phase1"
        }
        
        # Execute
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Verify UPDATE was called (not INSERT)
        update_found = False
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "UPDATE knowledge_base" in sql:
                params = call_args[0][1]
                new_confidence = params[0]
                
                # Confidence should have increased
                assert new_confidence > existing_pattern['confidence']
                assert new_confidence <= 1.0
                
                update_found = True
                break
        
        assert update_found, "UPDATE query not found"
    
    def test_high_confidence_converts_to_deterministic(self, wowvision_agent, caplog):
        """Test that high-confidence patterns trigger deterministic rule conversion"""
        # Setup - Mock existing pattern with 0.85 confidence
        # After update with alpha=0.2, new confidence = 0.85 + 0.2*(1.0-0.85) = 0.88
        # We need to start higher to reach 0.9+
        cursor = wowvision_agent.db.cursor.return_value
        cursor.fetchone.return_value = (
            1,
            "Allow python_in_phase1",
            json.dumps({"violation_type": "python_in_phase1", "outcome": "approved"}),
            0.88  # High enough that update will push it over 0.9
        )
        
        decision = Decision(
            approved=False,
            reason="Python in Phase 1",
            confidence=0.9,
            method="llm"  # Must be LLM for conversion
        )
        
        feedback = {
            "reasoning": "Test fixture",
            "decided_by": "developer",
            "file_path": "tests/fixture.py",
            "violation_type": "python_in_phase1"
        }
        
        # Set log level to INFO to capture the messages
        import logging
        logging.getLogger("waooaw.agents.base_agent").setLevel(logging.INFO)
        
        # Execute
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Verify conversion message in logs
        # With 0.88 + 0.2*(1.0-0.88) = 0.904, should trigger conversion
        assert ("Converting to deterministic rule" in caplog.text or 
                "Pattern ready for deterministic" in caplog.text)
    
    def test_extract_learning_pattern(self, wowvision_agent):
        """Test pattern extraction from decision and feedback"""
        decision = Decision(
            approved=False,
            reason="Brand tagline incorrect",
            confidence=0.9,
            method="deterministic",
            citations=["BRAND_STRATEGY.md"]
        )
        
        feedback = {
            "reasoning": "Tagline should be 'Agents Earn Your Business'",
            "decided_by": "brand-manager",
            "file_path": "frontend/index.html",
            "violation_type": "brand_violation"
        }
        
        # Execute
        pattern = wowvision_agent._extract_learning_pattern(decision, "rejected", feedback)
        
        # Verify pattern structure
        assert pattern is not None
        assert pattern['title'] == "Reject brand_violation"
        assert pattern['violation_type'] == "brand_violation"
        assert pattern['outcome'] == "rejected"
        assert pattern['learned_from'] == "brand-manager"
        assert 'rule' in pattern
        assert 'examples' in pattern
        assert len(pattern['examples']) > 0
    
    def test_calculate_confidence_increase(self, wowvision_agent):
        """Test confidence increase calculation"""
        # Test positive reinforcement
        new_confidence = wowvision_agent._calculate_updated_confidence(
            current_confidence=0.7,
            outcome="approved",
            decision_confidence=0.85
        )
        
        assert new_confidence > 0.7  # Should increase
        assert new_confidence <= 1.0  # Should be clamped
    
    def test_calculate_confidence_decrease(self, wowvision_agent):
        """Test confidence decrease for modified outcomes"""
        # Test refinement needed
        new_confidence = wowvision_agent._calculate_updated_confidence(
            current_confidence=0.8,
            outcome="modify",
            decision_confidence=0.7
        )
        
        assert new_confidence < 0.8  # Should decrease
        assert new_confidence >= 0.1  # Should be clamped at minimum


# ============================================================================
# STORY 4.2: INTEGRATION WITH ESCALATION PROCESSING
# ============================================================================

class TestStory42EscalationIntegration:
    """Test integration of learning with escalation processing"""
    
    def test_escalation_triggers_learning(self, wowvision_agent, mock_github_client):
        """Test that processing escalation triggers learning"""
        # Setup escalation with original decision
        escalation_id = 1
        issue_number = 300
        
        # Mock escalation data in database
        cursor = wowvision_agent.db.cursor.return_value
        
        # First fetchone call - for getting original decision
        cursor.fetchone.return_value = (
            json.dumps({
                "filename": "tests/sample.py",
                "decision": {
                    "approved": False,
                    "reason": "Python file in Phase 1",
                    "confidence": 0.85,
                    "method": "llm",
                    "citations": []
                }
            }),
        )
        
        # Setup GitHub issue with decision
        mock_comment = Mock()
        mock_comment.body = "APPROVE: This is a test fixture"
        mock_comment.user.login = "dlai-sd"
        mock_comment.created_at = datetime(2025, 12, 27, 10, 0, 0)
        
        mock_issue = Mock()
        mock_issue.number = issue_number
        mock_issue.html_url = f"https://github.com/test/repo/issues/{issue_number}"
        mock_issue.get_comments.return_value = [mock_comment]
        mock_issue.edit = Mock()
        
        mock_github_client.get_issue.return_value = mock_issue
        
        escalation_data = {
            "escalation": {
                "id": escalation_id,
                "issue_number": issue_number,
                "agent_id": "WowVision-Prime",
                "reason": "Python file in Phase 1"
            }
        }
        
        # Execute
        wowvision_agent._process_escalation(escalation_data)
        
        # Verify learning was triggered (INSERT or UPDATE to knowledge_base)
        learning_found = False
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "knowledge_base" in sql and ("INSERT" in sql or "UPDATE" in sql):
                learning_found = True
                break
        
        assert learning_found, "Learning was not triggered during escalation processing"
    
    def test_get_original_decision(self, wowvision_agent):
        """Test retrieving original decision from escalation"""
        # Setup
        escalation_id = 1
        cursor = wowvision_agent.db.cursor.return_value
        cursor.fetchone.return_value = (
            json.dumps({
                "filename": "app/test.py",
                "decision": {
                    "approved": False,
                    "reason": "Python in Phase 1",
                    "confidence": 0.9,
                    "method": "deterministic"
                }
            }),
        )
        
        # Execute
        decision = wowvision_agent._get_original_decision(escalation_id)
        
        # Verify
        assert decision is not None
        assert decision['approved'] == False
        assert decision['reason'] == "Python in Phase 1"
        assert decision['confidence'] == 0.9
        assert decision['file_path'] == "app/test.py"
        assert decision['violation_type'] == "python_in_phase1"
    
    def test_classify_violation_type(self, wowvision_agent):
        """Test violation type classification"""
        test_cases = [
            ("app/main.py", "Python file in Phase 1", "python_in_phase1"),
            ("docs/README.md", "Missing content", "documentation"),
            ("config.yaml", "Invalid config", "configuration"),
            ("frontend/index.html", "Wrong brand tagline", "brand_violation"),
            ("docs/vision.md", "Violates vision", "vision_violation"),
            ("app/unknown.txt", "Some error", "unknown_violation"),
        ]
        
        for filename, reason, expected_type in test_cases:
            result = wowvision_agent._classify_violation_type(filename, reason)
            assert result == expected_type, f"Failed for {filename}: expected {expected_type}, got {result}"


# ============================================================================
# STORY 4.2: ACCEPTANCE CRITERIA TESTS
# ============================================================================

class TestStory42AcceptanceCriteria:
    """Test acceptance criteria for Story 4.2"""
    
    def test_ac1_patterns_saved_to_knowledge_base(self, wowvision_agent):
        """AC: Patterns saved to knowledge_base table"""
        decision = Decision(
            approved=False,
            reason="Test violation",
            confidence=0.8,
            method="llm"
        )
        
        feedback = {
            "reasoning": "This is acceptable",
            "decided_by": "reviewer",
            "file_path": "test.py",
            "violation_type": "test_violation"
        }
        
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Verify INSERT to knowledge_base
        cursor = wowvision_agent.db.cursor.return_value
        insert_found = False
        for call_args in cursor.execute.call_args_list:
            sql = call_args[0][0]
            if "INSERT INTO knowledge_base" in sql:
                insert_found = True
                break
        
        assert insert_found
        assert wowvision_agent.db.commit.called
    
    def test_ac2_confidence_updated_correctly(self, wowvision_agent):
        """AC: Confidence updated correctly for similar patterns"""
        # Test confidence increase
        new_conf = wowvision_agent._calculate_updated_confidence(0.7, "approved", 0.8)
        assert new_conf > 0.7
        
        # Test confidence decrease
        new_conf = wowvision_agent._calculate_updated_confidence(0.8, "modify", 0.7)
        assert new_conf < 0.8
        
        # Test clamping
        new_conf = wowvision_agent._calculate_updated_confidence(0.95, "approved", 0.9)
        assert new_conf <= 1.0
    
    def test_ac3_deterministic_rules_created(self, wowvision_agent, caplog):
        """AC: Deterministic rules created when confidence >0.9"""
        # Mock existing high-confidence pattern
        cursor = wowvision_agent.db.cursor.return_value
        cursor.fetchone.return_value = (
            1,
            "Allow test_violation",
            json.dumps({"violation_type": "test", "outcome": "approved"}),
            0.88
        )
        
        decision = Decision(
            approved=False,
            reason="Test",
            confidence=0.92,
            method="llm"
        )
        
        feedback = {
            "reasoning": "OK",
            "decided_by": "dev",
            "file_path": "test.py",
            "violation_type": "test"
        }
        
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Should trigger conversion
        assert "Converting to deterministic rule" in caplog.text or \
               "Pattern ready for deterministic" in caplog.text
    
    def test_ac4_learning_logged(self, wowvision_agent, caplog):
        """AC: Learning logged (observability)"""
        decision = Decision(
            approved=False,
            reason="Test",
            confidence=0.8,
            method="llm"
        )
        
        feedback = {
            "reasoning": "OK",
            "decided_by": "dev",
            "file_path": "test.py",
            "violation_type": "test"
        }
        
        wowvision_agent.learn_from_outcome(decision, "approved", feedback)
        
        # Verify logging
        assert "📚" in caplog.text  # Learning emoji
        assert "learning" in caplog.text.lower() or "learned" in caplog.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
