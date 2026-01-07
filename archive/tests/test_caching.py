"""
Unit Tests for LLM Caching & Cost Tracking - Story 3.4
"""
import pytest
import time

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.llm.caching import (
    CacheHierarchy,
    LLMCostTracker,
    generate_cache_key
)


class TestCacheHierarchy:
    """Test multi-tier cache."""
    
    def test_init(self):
        """Should initialize cache."""
        cache = CacheHierarchy(memory_max_size=50, default_ttl=60)
        
        assert cache.memory_max_size == 50
        assert cache.default_ttl == 60
        assert cache.hits == 0
        assert cache.misses == 0
    
    def test_set_and_get(self):
        """Should store and retrieve values."""
        cache = CacheHierarchy()
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        
        assert value == "value1"
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_cache_miss(self):
        """Should return None on miss."""
        cache = CacheHierarchy()
        
        value = cache.get("nonexistent")
        
        assert value is None
        assert cache.misses == 1
    
    def test_ttl_expiration(self):
        """Should expire entries after TTL."""
        cache = CacheHierarchy(default_ttl=1)
        
        cache.set("key1", "value1", ttl=1)
        
        # Immediate retrieval should work
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("key1") is None
    
    def test_lru_eviction(self):
        """Should evict LRU when at capacity."""
        cache = CacheHierarchy(memory_max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 (make it more recently used)
        cache.get("key1")
        
        # Add key3 (should evict key2)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key3") == "value3"  # Newly added
        assert cache.get("key2") is None  # Evicted
    
    def test_invalidate(self):
        """Should invalidate entries."""
        cache = CacheHierarchy()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.invalidate("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Should clear all entries."""
        cache = CacheHierarchy()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache.memory_cache) == 0
    
    def test_hit_rate_tracking(self):
        """Should track hit rate."""
        cache = CacheHierarchy()
        
        # 3 sets
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 2 hits, 1 miss
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("key9")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_pct"] == 66.67


class TestLLMCostTracker:
    """Test cost tracking."""
    
    def test_init(self):
        """Should initialize cost tracker."""
        tracker = LLMCostTracker(daily_budget=50.0)
        
        assert tracker.daily_budget == 50.0
        assert tracker.total_cost == 0.0
    
    def test_track_request(self):
        """Should track request cost."""
        tracker = LLMCostTracker()
        
        result = tracker.track_request(
            model="claude-sonnet-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert result["input_tokens"] == 1000
        assert result["output_tokens"] == 500
        assert result["total_cost"] > 0
        assert tracker.requests_count == 1
    
    def test_cost_calculation(self):
        """Should calculate cost correctly."""
        tracker = LLMCostTracker()
        
        # Claude Sonnet 4: $3/1M input, $15/1M output
        result = tracker.track_request(
            model="claude-sonnet-4",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        
        # Should be $3 input + $15 output = $18
        assert result["input_cost"] == 3.0
        assert result["output_cost"] == 15.0
        assert result["total_cost"] == 18.0
    
    def test_budget_check(self):
        """Should check budget."""
        tracker = LLMCostTracker(daily_budget=1.0)
        
        # Small request (under budget)
        tracker.track_request("claude-sonnet-4", 1000, 500)
        assert tracker.check_budget() is True
        
        # Large request (exceed budget)
        tracker.track_request("claude-sonnet-4", 1_000_000, 1_000_000)
        assert tracker.check_budget() is False
    
    def test_budget_status(self):
        """Should report budget status."""
        tracker = LLMCostTracker(daily_budget=10.0)
        
        tracker.track_request("claude-sonnet-4", 100_000, 50_000)
        
        status = tracker.get_budget_status()
        assert status["daily_budget"] == 10.0
        assert status["daily_cost"] > 0
        assert status["daily_remaining"] < 10.0
        assert "pct_used" in status
    
    def test_total_stats(self):
        """Should report total statistics."""
        tracker = LLMCostTracker()
        
        tracker.track_request("claude-sonnet-4", 1000, 500)
        tracker.track_request("claude-sonnet-4", 2000, 1000)
        
        stats = tracker.get_total_stats()
        assert stats["total_requests"] == 2
        assert stats["total_input_tokens"] == 3000
        assert stats["total_output_tokens"] == 1500
        assert stats["avg_cost_per_request"] > 0


class TestCacheKeyGeneration:
    """Test cache key generation."""
    
    def test_generate_key(self):
        """Should generate consistent key."""
        key1 = generate_cache_key("prompt1", "model1")
        key2 = generate_cache_key("prompt1", "model1")
        
        assert key1 == key2
    
    def test_different_prompts(self):
        """Should generate different keys for different prompts."""
        key1 = generate_cache_key("prompt1", "model1")
        key2 = generate_cache_key("prompt2", "model1")
        
        assert key1 != key2
    
    def test_with_kwargs(self):
        """Should include kwargs in key."""
        key1 = generate_cache_key("prompt", "model", temperature=0.7)
        key2 = generate_cache_key("prompt", "model", temperature=0.9)
        
        assert key1 != key2
    
    def test_key_length(self):
        """Should generate reasonable key length."""
        key = generate_cache_key("test prompt", "model")
        
        assert len(key) == 16  # First 16 chars of SHA256


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
