"""
Unit Tests for Claude API Wrapper - Story 3.1

Tests ClaudeAPIWrapper with mocked Anthropic client.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from anthropic import RateLimitError, APIError, APIConnectionError

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.llm.claude_wrapper import ClaudeAPIWrapper


class TestClaudeAPIWrapper:
    """Test Claude API wrapper."""
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_init(self, mock_anthropic_class):
        """Should initialize with API key."""
        wrapper = ClaudeAPIWrapper(model="claude-3-opus", max_tokens=8192)
        
        assert wrapper.model == "claude-3-opus"
        assert wrapper.max_tokens == 8192
        assert wrapper.total_calls == 0
        mock_anthropic_class.assert_called_once_with(api_key="test_key")
    
    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """Should raise error if no API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            ClaudeAPIWrapper()
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_simple_call(self, mock_anthropic_class):
        """Should make simple API call."""
        # Mock response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello! How can I help?")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        response = wrapper.simple_call("Hello Claude!")
        
        assert response == "Hello! How can I help?"
        assert wrapper.total_calls == 1
        assert wrapper.total_input_tokens == 10
        assert wrapper.total_output_tokens == 20
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_call_with_system_prompt(self, mock_anthropic_class):
        """Should include system prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I'm a helpful assistant")]
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        result = wrapper.call(
            messages=[{"role": "user", "content": "Who are you?"}],
            system="You are a helpful AI assistant"
        )
        
        assert result["content"] == "I'm a helpful assistant"
        assert result["usage"]["input_tokens"] == 15
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["system"] == "You are a helpful AI assistant"
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_multi_turn_conversation(self, mock_anthropic_class):
        """Should handle multi-turn conversation."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="The capital is Paris")]
        mock_response.usage.input_tokens = 30
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        conversation = [
            {"role": "user", "content": "What is France?"},
            {"role": "assistant", "content": "France is a country in Europe"},
            {"role": "user", "content": "What is its capital?"}
        ]
        
        response = wrapper.multi_turn_call(conversation)
        
        assert response == "The capital is Paris"
        assert wrapper.total_calls == 1
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    @patch("waooaw.llm.claude_wrapper.time.time")
    def test_latency_tracking(self, mock_time, mock_anthropic_class):
        """Should track API call latency."""
        mock_time.side_effect = [0.0, 1.5]  # 1.5 second latency
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        result = wrapper.simple_call("Test")
        
        assert result == "Response"
        # Latency should be tracked in full call() response
        full_result = wrapper.call(messages=[{"role": "user", "content": "Test"}])
        assert "latency_ms" in full_result
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_usage_stats(self, mock_anthropic_class):
        """Should track cumulative usage."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        
        # Make 3 calls
        for _ in range(3):
            wrapper.simple_call("Test")
        
        stats = wrapper.get_usage_stats()
        assert stats["total_calls"] == 3
        assert stats["input_tokens"] == 300
        assert stats["output_tokens"] == 150
        assert stats["total_tokens"] == 450
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_reset_usage_stats(self, mock_anthropic_class):
        """Should reset usage counters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        wrapper.simple_call("Test")
        
        assert wrapper.total_calls == 1
        
        wrapper.reset_usage_stats()
        
        assert wrapper.total_calls == 0
        assert wrapper.total_input_tokens == 0
        assert wrapper.total_output_tokens == 0
    
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    @patch("waooaw.llm.claude_wrapper.Anthropic")
    def test_api_error_handling(self, mock_anthropic_class):
        """Should propagate API errors."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = APIError("API Error")
        mock_anthropic_class.return_value = mock_client
        
        wrapper = ClaudeAPIWrapper()
        
        with pytest.raises(APIError):
            wrapper.simple_call("Test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
