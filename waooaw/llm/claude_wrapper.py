"""
Claude API Wrapper - Story 3.1

Wrapper for Anthropic Claude API with retries, rate limiting, and error handling.
Part of Epic 3: LLM Integration.
"""
import logging
import time
import os
from typing import List, Dict, Optional, Any
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError
import backoff

logger = logging.getLogger(__name__)


class ClaudeAPIWrapper:
    """
    Wrapper for Claude API with resilience features.
    
    Features:
    - Exponential backoff for retries
    - Rate limit handling
    - Token usage tracking
    - Structured error handling
    - Streaming support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Initialize Claude API wrapper.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        
        logger.info(
            f"ClaudeAPIWrapper initialized: model={model}, max_tokens={max_tokens}"
        )
    
    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, APIConnectionError),
        max_tries=5,
        max_time=300  # 5 minutes max
    )
    def call(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Claude API with automatic retries.
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            system: System prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            **kwargs: Additional API parameters
            
        Returns:
            Dict with 'content', 'usage', 'model', 'stop_reason'
            
        Raises:
            APIError: If API call fails after retries
        """
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system if system else None,
                messages=messages,
                **kwargs
            )
            
            latency = time.time() - start_time
            
            # Track usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
            self.total_calls += 1
            
            logger.info(
                f"Claude API call successful",
                extra={
                    "model": response.model,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "latency_ms": int(latency * 1000),
                    "stop_reason": response.stop_reason
                }
            )
            
            return {
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "stop_reason": response.stop_reason,
                "latency_ms": int(latency * 1000)
            }
            
        except RateLimitError as e:
            logger.warning(f"Rate limit hit, will retry: {e}")
            raise  # backoff will handle retry
            
        except APIConnectionError as e:
            logger.warning(f"Connection error, will retry: {e}")
            raise  # backoff will handle retry
            
        except APIError as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise
    
    def simple_call(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simplified API call with just a prompt string.
        
        Args:
            prompt: User prompt
            system: System prompt
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.call(messages=messages, system=system, **kwargs)
        return response["content"]
    
    def multi_turn_call(
        self,
        conversation: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Multi-turn conversation.
        
        Args:
            conversation: List of turns [{"role": "user"/"assistant", "content": "..."}]
            system: System prompt
            **kwargs: Additional parameters
            
        Returns:
            Assistant's response
        """
        response = self.call(messages=conversation, system=system, **kwargs)
        return response["content"]
    
    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get cumulative usage statistics.
        
        Returns:
            Dict with total_calls, input_tokens, output_tokens, total_tokens
        """
        return {
            "total_calls": self.total_calls,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }
    
    def reset_usage_stats(self):
        """Reset usage counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        logger.info("Usage stats reset")
