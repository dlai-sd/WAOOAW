"""
Embedding Cache - Redis-backed cache with 24hr TTL

Architecture: Content-addressed cache using SHA-256 hash of text
Reference: PLANT_BLUEPRINT Section 9.5 (Redis for embedding cache)
"""

import redis
import hashlib
import json
from typing import List, Optional
import logging

from core.config import settings


logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Redis-backed cache for ML embeddings.
    
    Responsibilities:
    - Cache embeddings by content hash (SHA-256)
    - 24-hour TTL (configurable)
    - Prevent redundant ML service calls
    - Cost optimization
    """
    
    def __init__(
        self,
        redis_url: str = None,
        ttl_seconds: int = None,
    ):
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = ttl_seconds or settings.redis_ttl_seconds
        
        self.client = redis.from_url(
            self.redis_url,
            decode_responses=True,
        )
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key from text + model."""
        content = f"{text}:{model}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"embedding:{content_hash}"
    
    def get(self, text: str, model: str = None) -> Optional[List[float]]:
        """
        Retrieve cached embedding.
        
        Args:
            text: Input text
            model: Model name (default: MiniLM-384)
        
        Returns:
            Cached embedding or None if not found
        """
        model = model or settings.ml_model
        cache_key = self._get_cache_key(text, model)
        
        try:
            cached_value = self.client.get(cache_key)
            if cached_value:
                embedding = json.loads(cached_value)
                logger.info(f"Cache HIT: {cache_key[:16]}...")
                return embedding
            else:
                logger.info(f"Cache MISS: {cache_key[:16]}...")
                return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None
    
    def set(
        self,
        text: str,
        embedding: List[float],
        model: str = None,
    ):
        """
        Store embedding in cache with TTL.
        
        Args:
            text: Input text
            embedding: Embedding vector (384 dims)
            model: Model name
        """
        model = model or settings.ml_model
        cache_key = self._get_cache_key(text, model)
        
        try:
            cached_value = json.dumps(embedding)
            self.client.setex(
                cache_key,
                self.ttl_seconds,
                cached_value,
            )
            logger.info(
                f"Cache SET: {cache_key[:16]}... "
                f"(TTL: {self.ttl_seconds}s, dims: {len(embedding)})"
            )
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
    
    def delete(self, text: str, model: str = None):
        """
        Delete cached embedding (used when invalidating stale embeddings).
        
        Args:
            text: Input text
            model: Model name
        """
        model = model or settings.ml_model
        cache_key = self._get_cache_key(text, model)
        
        try:
            self.client.delete(cache_key)
            logger.info(f"Cache DELETE: {cache_key[:16]}...")
        except Exception as e:
            logger.error(f"Cache deletion error: {str(e)}")
    
    def flush_all(self):
        """
        Flush all cached embeddings (dangerous - use only in testing).
        """
        try:
            keys = self.client.keys("embedding:*")
            if keys:
                self.client.delete(*keys)
                logger.warning(f"Cache FLUSH: deleted {len(keys)} embeddings")
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
