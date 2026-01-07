"""
WAOOAW Common Components: Cache

Provides 3-level cache hierarchy (L1 memory, L2 Redis, L3 PostgreSQL)
with automatic promotion/demotion and SimpleCache for basic use cases.

Usage:
    # Simple use case (80%):
    cache = SimpleCache(max_size=1000)
    value = cache.get("key", default=None)
    cache.set("key", value, ttl=3600)
    
    # Advanced use case (20%):
    cache = CacheHierarchy(
        l1_max_size=1000,
        l2_ttl=300,
        l3_ttl=3600
    )
    value = cache.get_or_compute(
        key="decision:123",
        compute_fn=lambda: expensive_operation(),
        ttl=3600
    )

Vision Compliance:
    ✅ Cost Optimization: 90% cache hit = 90% free (no LLM calls)
    ✅ Zero Risk: Graceful degradation (cache miss → compute)
    ✅ Simplicity: SimpleCache for basic use, CacheHierarchy optional
"""

import time
import json
import logging
from typing import Any, Optional, Callable, Dict, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple LRU cache with TTL support.
    
    Perfect for 80% of use cases that don't need Redis/PostgreSQL.
    
    Example:
        cache = SimpleCache(max_size=1000)
        cache.set("key", "value", ttl=3600)
        value = cache.get("key", default=None)
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize simple cache.
        
        Args:
            max_size: Maximum number of items in cache (LRU eviction)
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[Any, Optional[float]]] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached value or default
        """
        if key not in self._cache:
            self._misses += 1
            return default
        
        value, expiry = self._cache[key]
        
        # Check TTL
        if expiry is not None and time.time() > expiry:
            del self._cache[key]
            self._misses += 1
            return default
        
        # Move to end (LRU)
        self._cache.move_to_end(key)
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiry)
        """
        expiry = time.time() + ttl if ttl else None
        
        # Update existing or add new
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, expiry)
        
        # Evict oldest if over size
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
    
    def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, hit_rate, size
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'size': len(self._cache),
            'max_size': self.max_size
        }


class CacheHierarchy:
    """
    3-level cache with automatic promotion/demotion.
    
    L1: In-memory (1ms, small, volatile)
    L2: Redis (10ms, medium, persistent)  
    L3: PostgreSQL (100ms, large, durable)
    
    Features:
    - Automatic promotion on cache hit (L3→L2→L1)
    - Automatic demotion on cache set (L1→L2→L3)
    - Graceful degradation (Redis down → L1+L3 only)
    - get_or_compute pattern for transparent caching
    
    Example:
        cache = CacheHierarchy(
            l1_max_size=1000,
            l2_ttl=300,
            l3_ttl=3600,
            redis_client=redis,
            db_connection=db
        )
        
        # Get with auto-promotion:
        value = cache.get("key")
        
        # Get or compute:
        value = cache.get_or_compute(
            key="expensive_key",
            compute_fn=lambda: expensive_operation(),
            ttl=3600
        )
    """
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_ttl: int = 300,
        l3_ttl: int = 3600,
        redis_client: Optional[Any] = None,
        db_connection: Optional[Any] = None,
        eviction_policy: str = "LRU"
    ):
        """
        Initialize cache hierarchy.
        
        Args:
            l1_max_size: Max items in L1 (memory)
            l2_ttl: TTL for L2 (Redis) in seconds
            l3_ttl: TTL for L3 (PostgreSQL) in seconds
            redis_client: Redis client instance (optional)
            db_connection: Database connection (optional)
            eviction_policy: "LRU" or custom (future)
        """
        self.l1 = SimpleCache(max_size=l1_max_size)
        self.l2_client = redis_client
        self.l2_ttl = l2_ttl
        self.l3_connection = db_connection
        self.l3_ttl = l3_ttl
        
        self._l2_available = redis_client is not None
        self._l3_available = db_connection is not None
        
        # Stats tracking
        self._l2_hits = 0
        self._l3_hits = 0
        
        logger.info(
            f"CacheHierarchy initialized: "
            f"L1={l1_max_size} items, "
            f"L2={'enabled' if self._l2_available else 'disabled'} (TTL={l2_ttl}s), "
            f"L3={'enabled' if self._l3_available else 'disabled'} (TTL={l3_ttl}s)"
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache hierarchy with automatic promotion.
        
        Flow:
        1. Check L1 (memory) - 1ms
        2. If miss, check L2 (Redis) - 10ms, promote to L1
        3. If miss, check L3 (PostgreSQL) - 100ms, promote to L2+L1
        4. If all miss, return default
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        # L1 check
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # L2 check (Redis)
        if self._l2_available:
            try:
                value = self._get_from_l2(key)
                if value is not None:
                    # Promote to L1
                    self._l2_hits += 1
                    self.l1.set(key, value, ttl=self.l2_ttl)
                    logger.debug(f"Cache L2 hit, promoted to L1: {key}")
                    return value
            except Exception as e:
                logger.warning(f"L2 cache error: {e}")
                self._l2_available = False
        
        # L3 check (PostgreSQL)
        if self._l3_available:
            try:
                value = self._get_from_l3(key)
                if value is not None:
                    # Promote to L2+L1
                    self._l3_hits += 1
                    if self._l2_available:
                        self._set_in_l2(key, value, ttl=self.l2_ttl)
                    self.l1.set(key, value, ttl=self.l3_ttl)
                    logger.debug(f"Cache L3 hit, promoted to L2+L1: {key}")
                    return value
            except Exception as e:
                logger.warning(f"L3 cache error: {e}")
                self._l3_available = False
        
        # All misses
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache hierarchy with automatic demotion.
        
        Writes to L1 immediately, asynchronously writes to L2+L3.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default L2/L3 TTLs if None)
        """
        # Write to L1 (always)
        l1_ttl = ttl if ttl else self.l2_ttl
        self.l1.set(key, value, ttl=l1_ttl)
        
        # Write to L2 (async, best-effort)
        if self._l2_available:
            try:
                l2_ttl = ttl if ttl else self.l2_ttl
                self._set_in_l2(key, value, ttl=l2_ttl)
            except Exception as e:
                logger.warning(f"L2 cache write failed: {e}")
                self._l2_available = False
        
        # Write to L3 (async, best-effort)
        if self._l3_available:
            try:
                l3_ttl = ttl if ttl else self.l3_ttl
                self._set_in_l3(key, value, ttl=l3_ttl)
            except Exception as e:
                logger.warning(f"L3 cache write failed: {e}")
                self._l3_available = False
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute if missing.
        
        This is the primary method for transparent caching.
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
            
        Example:
            value = cache.get_or_compute(
                key="decision:123",
                compute_fn=lambda: expensive_llm_call(),
                ttl=3600
            )
        """
        # Try to get from cache
        value = self.get(key)
        
        if value is not None:
            return value
        
        # Compute value
        logger.debug(f"Cache miss, computing: {key}")
        value = compute_fn()
        
        # Store in cache
        self.set(key, value, ttl=ttl)
        
        return value
    
    def delete(self, key: str):
        """Delete key from all cache levels."""
        self.l1.delete(key)
        
        if self._l2_available:
            try:
                self._delete_from_l2(key)
            except Exception as e:
                logger.warning(f"L2 delete failed: {e}")
        
        if self._l3_available:
            try:
                self._delete_from_l3(key)
            except Exception as e:
                logger.warning(f"L3 delete failed: {e}")
    
    def clear(self):
        """Clear all cache levels."""
        self.l1.clear()
        
        if self._l2_available:
            try:
                # Redis flushdb is dangerous, skip for now
                logger.warning("L2 clear not implemented (use Redis FLUSHDB manually)")
            except Exception as e:
                logger.warning(f"L2 clear failed: {e}")
        
        if self._l3_available:
            try:
                cursor = self.l3_connection.cursor()
                cursor.execute("DELETE FROM cache_l3")
                self.l3_connection.commit()
                cursor.close()
            except Exception as e:
                logger.warning(f"L3 clear failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all cache levels.
        
        Returns:
            Dict with L1/L2/L3 stats (flattened)
        """
        l1_stats = self.l1.get_stats()
        
        stats = {
            'l1_hits': l1_stats['hits'],
            'l1_misses': l1_stats['misses'],
            'l1_hit_rate': l1_stats['hit_rate'],
            'l1_size': l1_stats['size'],
            'l2_hits': self._l2_hits,
            'l2_available': self._l2_available,
            'l2_ttl': self.l2_ttl,
            'l3_hits': self._l3_hits,
            'l3_available': self._l3_available,
            'l3_ttl': self.l3_ttl
        }
        
        return stats
    
    # Private methods for L2/L3 operations
    
    def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get value from Redis (L2)."""
        if not self.l2_client:
            return None
        
        data = self.l2_client.get(key)
        if data is None:
            return None
        
        # Deserialize
        try:
            return json.loads(data)
        except:
            return data
    
    def _set_in_l2(self, key: str, value: Any, ttl: int):
        """Set value in Redis (L2)."""
        if not self.l2_client:
            return
        
        # Serialize
        try:
            data = json.dumps(value)
        except:
            data = str(value)
        
        self.l2_client.setex(key, ttl, data)
    
    def _delete_from_l2(self, key: str):
        """Delete key from Redis (L2)."""
        if self.l2_client:
            self.l2_client.delete(key)
    
    def _get_from_l3(self, key: str) -> Optional[Any]:
        """Get value from PostgreSQL (L3)."""
        if not self.l3_connection:
            return None
        
        cursor = self.l3_connection.cursor()
        cursor.execute(
            """
            SELECT value, expires_at 
            FROM cache_l3 
            WHERE key = %s
            """,
            (key,)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        value_json, expires_at = row
        
        # Check expiry
        if expires_at and datetime.now() > expires_at:
            self._delete_from_l3(key)
            return None
        
        # Deserialize
        try:
            return json.loads(value_json)
        except:
            return value_json
    
    def _set_in_l3(self, key: str, value: Any, ttl: int):
        """Set value in PostgreSQL (L3)."""
        if not self.l3_connection:
            return
        
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Serialize
        try:
            value_json = json.dumps(value)
        except:
            value_json = str(value)
        
        cursor = self.l3_connection.cursor()
        cursor.execute(
            """
            INSERT INTO cache_l3 (key, value, expires_at, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (key) 
            DO UPDATE SET 
                value = EXCLUDED.value,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            """,
            (key, value_json, expires_at, datetime.now())
        )
        self.l3_connection.commit()
        cursor.close()
    
    def _delete_from_l3(self, key: str):
        """Delete key from PostgreSQL (L3)."""
        if not self.l3_connection:
            return
        
        cursor = self.l3_connection.cursor()
        cursor.execute("DELETE FROM cache_l3 WHERE key = %s", (key,))
        self.l3_connection.commit()
        cursor.close()
