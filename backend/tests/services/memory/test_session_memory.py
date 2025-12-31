"""
Unit tests for Session Memory Manager.

Tests cover:
- Store and retrieve interactions
- TTL management (trial vs paid)
- Context formatting
- Session stats
- Error handling
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from redis.asyncio import Redis

from app.services.memory.session_memory import (
    SessionMemoryManager,
    Interaction,
    build_contextualized_prompt
)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock(spec=Redis)
    redis.lpush = AsyncMock(return_value=1)
    redis.ltrim = AsyncMock(return_value=True)
    redis.expire = AsyncMock(return_value=True)
    redis.lrange = AsyncMock(return_value=[])
    redis.delete = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=604800)
    return redis


@pytest.fixture
def memory_manager(mock_redis):
    """SessionMemoryManager instance with mocked Redis."""
    return SessionMemoryManager(mock_redis)


@pytest.fixture
def sample_interaction():
    """Sample interaction for testing."""
    return Interaction(
        task_type="create_social_post",
        task_input="Create LinkedIn post about AI in healthcare",
        agent_output="🏥 AI is transforming healthcare...",
        rating=5,
        duration_ms=1200,
        agent_id="agent_marketing_001",
        success=True
    )


class TestSessionMemoryManager:
    """Test suite for SessionMemoryManager."""
    
    @pytest.mark.asyncio
    async def test_store_interaction_trial(self, memory_manager, mock_redis, sample_interaction):
        """Test storing interaction for trial customer."""
        customer_id = "cust_123"
        
        await memory_manager.store_interaction(customer_id, sample_interaction, is_trial=True)
        
        # Verify Redis calls
        expected_key = "session:cust_123"
        mock_redis.lpush.assert_called_once()
        assert mock_redis.lpush.call_args[0][0] == expected_key
        
        mock_redis.ltrim.assert_called_once_with(expected_key, 0, 9)
        mock_redis.expire.assert_called_once_with(expected_key, 604800)  # 7 days
    
    @pytest.mark.asyncio
    async def test_store_interaction_paid(self, memory_manager, mock_redis, sample_interaction):
        """Test storing interaction for paid customer."""
        customer_id = "cust_456"
        
        await memory_manager.store_interaction(customer_id, sample_interaction, is_trial=False)
        
        # Verify TTL is 30 days for paid
        expected_key = "session:cust_456"
        mock_redis.expire.assert_called_once_with(expected_key, 2592000)  # 30 days
    
    @pytest.mark.asyncio
    async def test_get_session_context(self, memory_manager, mock_redis, sample_interaction):
        """Test retrieving session context."""
        customer_id = "cust_789"
        
        # Mock Redis returning 3 interactions
        interactions_data = [
            sample_interaction.model_dump_json(),
            sample_interaction.model_dump_json(),
            sample_interaction.model_dump_json(),
        ]
        mock_redis.lrange.return_value = interactions_data
        
        result = await memory_manager.get_session_context(customer_id, limit=10)
        
        assert len(result) == 3
        assert all(isinstance(i, Interaction) for i in result)
        mock_redis.lrange.assert_called_once_with("session:cust_789", 0, 9)
    
    @pytest.mark.asyncio
    async def test_get_session_context_empty(self, memory_manager, mock_redis):
        """Test retrieving context when no interactions exist."""
        customer_id = "cust_new"
        mock_redis.lrange.return_value = []
        
        result = await memory_manager.get_session_context(customer_id)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_last_n_context_formatted(self, memory_manager, mock_redis):
        """Test formatted context string for prompt injection."""
        customer_id = "cust_abc"
        
        # Create test interactions
        interactions = [
            Interaction(
                task_type="email_campaign",
                task_input="Create welcome email series",
                agent_output="Subject: Welcome to our platform! Email 1...",
                rating=5,
                agent_id="agent_marketing_002",
                success=True
            ),
            Interaction(
                task_type="social_post",
                task_input="Instagram post for product launch",
                agent_output="🚀 Launching today! Check out our new...",
                rating=4,
                agent_id="agent_marketing_001",
                success=True
            )
        ]
        
        mock_redis.lrange.return_value = [i.model_dump_json() for i in interactions]
        
        context = await memory_manager.get_last_n_context(customer_id, n=2)
        
        assert "email_campaign" in context
        assert "social_post" in context
        assert "agent_marketing_002" in context
        assert "✅" in context
        assert "⭐⭐⭐⭐⭐" in context  # 5 stars
    
    @pytest.mark.asyncio
    async def test_get_last_n_context_no_history(self, memory_manager, mock_redis):
        """Test context when customer has no history."""
        customer_id = "cust_new"
        mock_redis.lrange.return_value = []
        
        context = await memory_manager.get_last_n_context(customer_id)
        
        assert context == "No previous interactions."
    
    @pytest.mark.asyncio
    async def test_clear_session(self, memory_manager, mock_redis):
        """Test clearing session (GDPR compliance)."""
        customer_id = "cust_delete"
        
        await memory_manager.clear_session(customer_id)
        
        mock_redis.delete.assert_called_once_with("session:cust_delete")
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, memory_manager, mock_redis):
        """Test session statistics calculation."""
        customer_id = "cust_stats"
        
        # Mock interactions with mixed success/failure
        interactions = [
            Interaction(
                task_type="test1",
                task_input="task1",
                agent_output="output1",
                rating=5,
                agent_id="agent_001",
                success=True
            ),
            Interaction(
                task_type="test2",
                task_input="task2",
                agent_output="output2",
                rating=3,
                agent_id="agent_002",
                success=True
            ),
            Interaction(
                task_type="test3",
                task_input="task3",
                agent_output="output3",
                rating=None,
                agent_id="agent_003",
                success=False
            ),
        ]
        
        mock_redis.lrange.return_value = [i.model_dump_json() for i in interactions]
        mock_redis.ttl.return_value = 500000
        
        stats = await memory_manager.get_session_stats(customer_id)
        
        assert stats["total_interactions"] == 3
        assert stats["success_rate"] == 2/3  # 2 out of 3 successful
        assert stats["avg_rating"] == 4.0  # (5 + 3) / 2
        assert stats["ttl_remaining_seconds"] == 500000
    
    @pytest.mark.asyncio
    async def test_get_session_stats_no_data(self, memory_manager, mock_redis):
        """Test stats when customer has no interactions."""
        customer_id = "cust_empty"
        mock_redis.lrange.return_value = []
        
        stats = await memory_manager.get_session_stats(customer_id)
        
        assert stats["total_interactions"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_rating"] == 0.0
    
    @pytest.mark.asyncio
    async def test_extend_ttl_trial_to_paid(self, memory_manager, mock_redis):
        """Test extending TTL when customer converts from trial to paid."""
        customer_id = "cust_convert"
        
        await memory_manager.extend_ttl(customer_id, is_trial=False)
        
        mock_redis.expire.assert_called_once_with("session:cust_convert", 2592000)
    
    @pytest.mark.asyncio
    async def test_max_interactions_limit(self, memory_manager, mock_redis, sample_interaction):
        """Test that only last 10 interactions are kept."""
        customer_id = "cust_limit"
        
        # Store 15 interactions
        for _ in range(15):
            await memory_manager.store_interaction(customer_id, sample_interaction)
        
        # Verify ltrim is called to keep only 10
        assert mock_redis.ltrim.call_count == 15
        # Last call should trim to 0-9 (10 items)
        last_call = mock_redis.ltrim.call_args
        assert last_call[0][1] == 0
        assert last_call[0][2] == 9
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self, memory_manager, mock_redis):
        """Test graceful handling of corrupted Redis data."""
        customer_id = "cust_corrupt"
        
        # Mock Redis returning invalid JSON
        mock_redis.lrange.return_value = [
            '{"valid": "data"}',  # Will fail Interaction validation
            'invalid json{',       # Will fail JSON parsing
            '{"task_type": "test", "task_input": "t", "agent_output": "o", "agent_id": "a", "success": true}'  # Valid
        ]
        
        # Should not raise exception
        result = await memory_manager.get_session_context(customer_id)
        
        # Should only return the valid interaction
        assert len(result) == 1


class TestContextBuilder:
    """Test prompt enhancement utilities."""
    
    def test_build_contextualized_prompt(self):
        """Test building prompt with context."""
        base_prompt = "Create a marketing email"
        industry = "Healthcare"
        company = "HealthTech Inc"
        session_context = "1. Previous task about product launch..."
        
        result = build_contextualized_prompt(
            base_prompt, industry, company, session_context
        )
        
        assert "Healthcare" in result
        assert "HealthTech Inc" in result
        assert "Previous task about product launch" in result
        assert "Create a marketing email" in result
        assert "CUSTOMER CONTEXT" in result
        assert "RECENT INTERACTIONS" in result
    
    def test_prompt_has_instructions(self):
        """Test that contextualized prompt includes usage instructions."""
        result = build_contextualized_prompt("task", "Industry", "Company", "context")
        
        assert "personalized" in result.lower()
        assert "reference previous interactions" in result.lower()
        assert "don't ask for information you already have" in result.lower()


class TestInteractionModel:
    """Test Interaction Pydantic model."""
    
    def test_interaction_creation(self):
        """Test creating Interaction with all fields."""
        interaction = Interaction(
            task_type="test",
            task_input="input",
            agent_output="output",
            rating=5,
            duration_ms=1000,
            agent_id="agent_123",
            success=True
        )
        
        assert interaction.task_type == "test"
        assert interaction.rating == 5
        assert interaction.success is True
        assert isinstance(interaction.timestamp, datetime)
    
    def test_interaction_defaults(self):
        """Test Interaction with default values."""
        interaction = Interaction(
            task_type="test",
            task_input="input",
            agent_output="output",
            agent_id="agent_123"
        )
        
        assert interaction.rating is None
        assert interaction.duration_ms is None
        assert interaction.success is True  # Default
        assert interaction.timestamp is not None
    
    def test_interaction_json_serialization(self):
        """Test JSON serialization with datetime."""
        interaction = Interaction(
            task_type="test",
            task_input="input",
            agent_output="output",
            agent_id="agent_123"
        )
        
        json_str = interaction.model_dump_json()
        data = json.loads(json_str)
        
        assert "timestamp" in data
        assert "task_type" in data
        assert data["task_type"] == "test"


# Integration test markers
@pytest.mark.integration
class TestSessionMemoryIntegration:
    """
    Integration tests requiring real Redis.
    Run with: pytest -m integration
    """
    
    @pytest.mark.asyncio
    async def test_real_redis_roundtrip(self):
        """Test actual Redis storage and retrieval."""
        # This would use a real Redis instance
        # Skip for unit tests, implement when Redis is available
        pytest.skip("Integration test - requires Redis")
