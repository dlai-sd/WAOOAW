"""
Embedding Service

Handles text embedding using OpenAI's text-embedding-3-small model.
Cost: $0.02 per 1M tokens (very affordable for knowledge base).
"""

from typing import List, Optional
import asyncio
from dataclasses import dataclass
import hashlib
import json


@dataclass
class EmbeddingResult:
    """Result of embedding operation"""
    text: str
    embedding: List[float]
    model: str
    tokens: int
    cached: bool = False


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Uses OpenAI's text-embedding-3-small:
    - Dimension: 1536
    - Cost: $0.02 per 1M tokens
    - Performance: Fast, high quality
    
    Includes caching to reduce API calls and costs.
    """
    
    MODEL = "text-embedding-3-small"
    DIMENSION = 1536
    MAX_TOKENS = 8191  # Max input tokens
    COST_PER_MILLION_TOKENS = 0.02
    
    def __init__(
        self,
        openai_client=None,
        cache: Optional[dict] = None
    ):
        """
        Initialize embedding service.
        
        Args:
            openai_client: OpenAI async client (optional, for testing)
            cache: Cache dict for embeddings (optional)
        """
        self.client = openai_client
        self.cache = cache if cache is not None else {}
        self._total_tokens = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    async def embed_text(
        self,
        text: str,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache (default: True)
            
        Returns:
            EmbeddingResult with embedding vector
        """
        # Check cache
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self.cache:
            self._cache_hits += 1
            cached_result = self.cache[cache_key]
            return EmbeddingResult(
                text=text,
                embedding=cached_result["embedding"],
                model=self.MODEL,
                tokens=cached_result["tokens"],
                cached=True
            )
        
        self._cache_misses += 1
        
        # Generate embedding
        if self.client is None:
            # Mock for testing
            embedding = self._generate_mock_embedding(text)
            tokens = len(text.split()) * 2  # Rough estimate
        else:
            # Real OpenAI API call
            response = await self.client.embeddings.create(
                model=self.MODEL,
                input=text,
                encoding_format="float"
            )
            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens
        
        self._total_tokens += tokens
        
        # Cache result
        if use_cache:
            self.cache[cache_key] = {
                "embedding": embedding,
                "tokens": tokens
            }
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self.MODEL,
            tokens=tokens,
            cached=False
        )
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        use_cache: bool = True
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Max texts per API call (default: 100)
            use_cache: Whether to use cache
            
        Returns:
            List of EmbeddingResults
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Embed each text (with caching)
            batch_tasks = [
                self.embed_text(text, use_cache=use_cache)
                for text in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic mock embedding for testing.
        
        Uses hash of text to create consistent 1536-dim vector.
        """
        # Use text hash as seed for deterministic generation
        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
        
        # Generate 1536 floats between -1 and 1
        embedding = []
        seed = text_hash
        for _ in range(self.DIMENSION):
            # Simple pseudo-random generator
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            value = (seed % 10000) / 5000.0 - 1.0  # Range: -1 to 1
            embedding.append(value)
        
        # Normalize to unit vector
        magnitude = sum(x * x for x in embedding) ** 0.5
        embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def get_stats(self) -> dict:
        """Get embedding statistics"""
        return {
            "total_tokens": self._total_tokens,
            "total_cost": self._total_tokens * self.COST_PER_MILLION_TOKENS / 1_000_000,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": (
                self._cache_hits / (self._cache_hits + self._cache_misses)
                if (self._cache_hits + self._cache_misses) > 0
                else 0.0
            )
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def estimate_cost(self, num_documents: int, avg_tokens_per_doc: int) -> float:
        """
        Estimate cost for embedding documents.
        
        Args:
            num_documents: Number of documents
            avg_tokens_per_doc: Average tokens per document
            
        Returns:
            Estimated cost in USD
        """
        total_tokens = num_documents * avg_tokens_per_doc
        return total_tokens * self.COST_PER_MILLION_TOKENS / 1_000_000


class EmbeddingCache:
    """
    Persistent embedding cache.
    
    In production, this would use Redis or database.
    For now, uses in-memory dict.
    """
    
    def __init__(self):
        self._cache: dict = {}
    
    def get(self, key: str) -> Optional[dict]:
        """Get cached embedding"""
        return self._cache.get(key)
    
    def set(self, key: str, value: dict):
        """Store embedding in cache"""
        self._cache[key] = value
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)
