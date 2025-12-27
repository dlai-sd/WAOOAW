"""
LLM Response Caching & Cost Optimization - Story 3.4

Multi-tier caching system with cost tracking.
Part of Epic 3: LLM Integration.
"""
import logging
import hashlib
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hit_count: int = 0
    last_accessed: float = 0


class CacheHierarchy:
    """
    Multi-tier cache: Memory → Redis → Disk
    
    Strategy:
    1. Check memory cache (fast, limited capacity)
    2. Check Redis cache (medium speed, shared)
    3. Fall back to LLM call
    4. Store in all tiers with TTL
    
    Features:
    - LRU eviction
    - TTL-based expiration
    - Hit rate tracking
    - Cost calculation
    """
    
    def __init__(
        self,
        memory_max_size: int = 100,
        default_ttl: int = 3600,
        enable_redis: bool = False
    ):
        """
        Initialize cache hierarchy.
        
        Args:
            memory_max_size: Max entries in memory cache
            default_ttl: Default TTL in seconds
            enable_redis: Enable Redis tier (requires redis client)
        """
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_max_size = memory_max_size
        self.default_ttl = default_ttl
        self.enable_redis = enable_redis
        self.redis_client = None
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.memory_hits = 0
        self.redis_hits = 0
        
        logger.info(
            f"CacheHierarchy initialized: memory_max={memory_max_size}, ttl={default_ttl}s, redis={enable_redis}"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if miss
        """
        # Check memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            
            # Check TTL
            if self._is_expired(entry):
                del self.memory_cache[key]
                logger.debug(f"Cache expired: {key}")
            else:
                entry.hit_count += 1
                entry.last_accessed = time.time()
                self.hits += 1
                self.memory_hits += 1
                logger.debug(f"Cache HIT (memory): {key}")
                return entry.value
        
        # Check Redis cache (if enabled)
        if self.enable_redis and self.redis_client:
            redis_value = self._get_from_redis(key)
            if redis_value is not None:
                # Promote to memory cache
                self.set(key, redis_value, ttl=self.default_ttl)
                self.hits += 1
                self.redis_hits += 1
                logger.debug(f"Cache HIT (redis): {key}")
                return redis_value
        
        # Cache miss
        self.misses += 1
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (default: self.default_ttl)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Evict if at capacity
        if len(self.memory_cache) >= self.memory_max_size:
            self._evict_lru()
        
        # Store in memory cache
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl,
            hit_count=0,
            last_accessed=time.time()
        )
        self.memory_cache[key] = entry
        
        # Store in Redis (if enabled)
        if self.enable_redis and self.redis_client:
            self._set_in_redis(key, value, ttl)
        
        logger.debug(f"Cache SET: {key} (ttl={ttl}s)")
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        if self.enable_redis and self.redis_client:
            self._delete_from_redis(key)
        
        logger.debug(f"Cache INVALIDATE: {key}")
    
    def clear(self) -> None:
        """Clear all cache."""
        self.memory_cache.clear()
        
        if self.enable_redis and self.redis_client:
            # Clear Redis keys with our prefix
            # (implementation depends on Redis setup)
            pass
        
        logger.info("Cache cleared")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        age = time.time() - entry.created_at
        return age > entry.ttl_seconds
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed
        )
        
        del self.memory_cache[lru_key]
        logger.debug(f"Cache EVICT (LRU): {lru_key}")
    
    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        # Placeholder for Redis integration
        return None
    
    def _set_in_redis(self, key: str, value: Any, ttl: int) -> None:
        """Set value in Redis cache."""
        # Placeholder for Redis integration
        pass
    
    def _delete_from_redis(self, key: str) -> None:
        """Delete value from Redis cache."""
        # Placeholder for Redis integration
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate_pct": round(hit_rate, 2),
            "memory_hits": self.memory_hits,
            "redis_hits": self.redis_hits,
            "memory_size": len(self.memory_cache),
            "memory_capacity": self.memory_max_size
        }


class LLMCostTracker:
    """
    Track LLM API costs and token usage.
    
    Features:
    - Token counting (input/output)
    - Cost calculation by model
    - Budget enforcement
    - Usage reporting
    """
    
    # Anthropic Claude pricing (per 1M tokens)
    PRICING = {
        "claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
    }
    
    def __init__(self, daily_budget: float = 100.0):
        """
        Initialize cost tracker.
        
        Args:
            daily_budget: Daily budget in USD
        """
        self.daily_budget = daily_budget
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.requests_count = 0
        
        # Daily tracking
        self.today = datetime.now().date()
        self.daily_cost = 0.0
        self.daily_requests = 0
        
        logger.info(f"LLMCostTracker initialized: daily_budget=${daily_budget}")
    
    def track_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Track LLM request cost.
        
        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Dict with cost breakdown
        """
        # Reset daily counters if new day
        self._check_new_day()
        
        # Get pricing
        pricing = self.PRICING.get(model, self.PRICING["claude-sonnet-4"])
        
        # Calculate cost (per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Update counters
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += total_cost
        self.requests_count += 1
        
        self.daily_cost += total_cost
        self.daily_requests += 1
        
        logger.info(
            f"LLM request: {model}, tokens={input_tokens}+{output_tokens}, cost=${total_cost:.4f}"
        )
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "model": model
        }
    
    def check_budget(self) -> bool:
        """
        Check if daily budget exceeded.
        
        Returns:
            True if under budget, False if exceeded
        """
        self._check_new_day()
        return self.daily_cost < self.daily_budget
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get budget status."""
        self._check_new_day()
        
        remaining = self.daily_budget - self.daily_cost
        pct_used = (self.daily_cost / self.daily_budget * 100) if self.daily_budget > 0 else 0
        
        return {
            "daily_budget": self.daily_budget,
            "daily_cost": round(self.daily_cost, 2),
            "daily_remaining": round(remaining, 2),
            "pct_used": round(pct_used, 2),
            "daily_requests": self.daily_requests,
            "under_budget": self.daily_cost < self.daily_budget
        }
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get lifetime statistics."""
        return {
            "total_requests": self.requests_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 2),
            "avg_cost_per_request": (
                round(self.total_cost / self.requests_count, 4)
                if self.requests_count > 0 else 0
            )
        }
    
    def _check_new_day(self) -> None:
        """Reset daily counters if new day."""
        today = datetime.now().date()
        if today != self.today:
            logger.info(
                f"New day: resetting daily counters. Yesterday: ${self.daily_cost:.2f}"
            )
            self.today = today
            self.daily_cost = 0.0
            self.daily_requests = 0


def generate_cache_key(prompt: str, model: str, **kwargs) -> str:
    """
    Generate cache key from prompt and parameters.
    
    Args:
        prompt: Prompt text
        model: Model name
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        Cache key (hex digest)
    """
    # Create deterministic key
    key_data = {
        "prompt": prompt,
        "model": model,
        **kwargs
    }
    
    # Sort keys for consistency
    key_str = json.dumps(key_data, sort_keys=True)
    
    # Hash
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]
