"""
Epic 3 Tests: LLM Integration & Decision Making

Comprehensive test suite covering Stories 3.1-3.6
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from waooaw.agents.base_agent import WAAOOWAgent, Decision
from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.agents.prompt_templates import (
    format_prompt,
    get_prompt_for_decision_type,
    ARCHITECTURE_VIOLATION_PROMPT,
    NAMING_CONVENTION_PROMPT,
)


# Fixtures
@pytest.fixture
def mock_db():
    """Mock PostgreSQL database"""
    db = Mock()
    cursor = Mock()
    cursor.fetchone = Mock(return_value={"failure_count": 0, "daily_cost": 0.0})
    cursor.fetchall = Mock(return_value=[])
    db.cursor = Mock(return_value=cursor)
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_llm():
    """Mock Claude API"""
    llm = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text='{"approved": true, "reason": "Looks good", "confidence": 0.95, "citations": ["doc.md"]}')]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    llm.messages = Mock()
    llm.messages.create = Mock(return_value=mock_response)
    return llm


@pytest.fixture
def base_agent(mock_db, mock_llm):
    """Base agent for testing"""
    with patch('waooaw.agents.base_agent.psycopg2.connect', return_value=mock_db):
        with patch('waooaw.agents.base_agent.Github'):
            agent = WAAOOWAgent(
                agent_id="test-agent",
                config={
                    "database_url": "postgresql://test",
                    "github_token": "test_token",
                    "github_repo": "dlai-sd/WAOOAW"
                }
            )
            agent.db = mock_db
            agent.llm = mock_llm
            return agent


# Story 3.1: LLM Integration Tests
class TestStory31LLMIntegration:
    """Tests for _call_llm() method"""
    
    def test_successful_llm_call(self, base_agent, mock_llm):
        """Test successful LLM call returns parsed response"""
        prompt = "Should we approve this file?"
        result = base_agent._call_llm(prompt)
        assert result["approved"] == True
        assert "reason" in result
        assert result["confidence"] > 0
        assert "cost" in result
        assert "tokens_used" in result
        mock_llm.messages.create.assert_called_once()


# Story 3.4: Prompt Templates Tests
class TestStory34PromptTemplates:
    """Tests for LLM prompt templates"""
    
    def test_architecture_violation_prompt_format(self):
        """Test architecture violation prompt formatting"""
        prompt = format_prompt(
            ARCHITECTURE_VIOLATION_PROMPT,
            file_path="frontend/index.html",
            author="developer",
            additions=50,
            deletions=10,
            phase="phase1_foundation",
            content_preview="Changed tagline to 'New Tagline'"
        )
        assert "frontend/index.html" in prompt
        assert "50 additions" in prompt
        assert "3-Layer Vision Stack" in prompt
