"""
Tests for Embedding Service
"""

import pytest
from app.services.knowledge.embeddings import (
    EmbeddingService,
    EmbeddingResult,
    EmbeddingCache
)


class TestEmbeddingService:
    """Test EmbeddingService functionality"""
    
    @pytest.mark.asyncio
    async def test_embed_text_basic(self):
        """Test basic text embedding"""
        service = EmbeddingService()
        
        result = await service.embed_text("Hello world")
        
        assert isinstance(result, EmbeddingResult)
        assert result.text == "Hello world"
        assert len(result.embedding) == 1536  # text-embedding-3-small dimension
        assert result.model == "text-embedding-3-small"
        assert result.tokens > 0
        assert result.cached is False
    
    @pytest.mark.asyncio
    async def test_embed_text_with_cache(self):
        """Test embedding with caching"""
        service = EmbeddingService()
        
        # First call
        result1 = await service.embed_text("Test text")
        assert result1.cached is False
        
        # Second call (should be cached)
        result2 = await service.embed_text("Test text")
        assert result2.cached is True
        assert result2.embedding == result1.embedding
        
        # Cache stats
        stats = service.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_hit_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_embed_text_deterministic(self):
        """Test mock embeddings are deterministic"""
        service = EmbeddingService()
        
        result1 = await service.embed_text("Same text", use_cache=False)
        result2 = await service.embed_text("Same text", use_cache=False)
        
        assert result1.embedding == result2.embedding
    
    @pytest.mark.asyncio
    async def test_embed_text_different_texts(self):
        """Test different texts produce different embeddings"""
        service = EmbeddingService()
        
        result1 = await service.embed_text("Text A")
        result2 = await service.embed_text("Text B")
        
        assert result1.embedding != result2.embedding
    
    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test batch embedding"""
        service = EmbeddingService()
        
        texts = ["Text 1", "Text 2", "Text 3"]
        results = await service.embed_batch(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, EmbeddingResult) for r in results)
        assert results[0].text == "Text 1"
        assert results[1].text == "Text 2"
        assert results[2].text == "Text 3"
    
    @pytest.mark.asyncio
    async def test_embed_batch_with_cache(self):
        """Test batch embedding uses cache"""
        service = EmbeddingService()
        
        texts = ["A", "B", "C"]
        
        # First batch
        await service.embed_batch(texts)
        
        # Second batch (should use cache)
        results = await service.embed_batch(texts)
        
        assert all(r.cached for r in results)
    
    def test_get_stats(self):
        """Test getting embedding statistics"""
        service = EmbeddingService()
        
        stats = service.get_stats()
        
        assert "total_tokens" in stats
        assert "total_cost" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "cache_hit_rate" in stats
        assert stats["total_cost"] >= 0
    
    def test_clear_cache(self):
        """Test clearing cache"""
        service = EmbeddingService()
        service._cache_hits = 10
        service._cache_misses = 5
        
        service.clear_cache()
        
        assert len(service.cache) == 0
        assert service._cache_hits == 0
        assert service._cache_misses == 0
    
    def test_estimate_cost(self):
        """Test cost estimation"""
        service = EmbeddingService()
        
        cost = service.estimate_cost(num_documents=100, avg_tokens_per_doc=500)
        
        # 100 docs * 500 tokens = 50,000 tokens
        # Cost: 50,000 * $0.02 / 1,000,000 = $0.001
        assert cost == pytest.approx(0.001, rel=0.01)
    
    def test_mock_embedding_normalized(self):
        """Test mock embeddings are unit vectors"""
        service = EmbeddingService()
        
        embedding = service._generate_mock_embedding("Test")
        
        # Check magnitude is ~1 (unit vector)
        magnitude = sum(x * x for x in embedding) ** 0.5
        assert magnitude == pytest.approx(1.0, rel=0.01)
    
    def test_mock_embedding_dimension(self):
        """Test mock embedding has correct dimension"""
        service = EmbeddingService()
        
        embedding = service._generate_mock_embedding("Test")
        
        assert len(embedding) == 1536


class TestEmbeddingCache:
    """Test EmbeddingCache"""
    
    def test_cache_get_set(self):
        """Test cache get/set"""
        cache = EmbeddingCache()
        
        cache.set("key1", {"embedding": [1, 2, 3], "tokens": 10})
        result = cache.get("key1")
        
        assert result is not None
        assert result["embedding"] == [1, 2, 3]
        assert result["tokens"] == 10
    
    def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = EmbeddingCache()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing cache"""
        cache = EmbeddingCache()
        cache.set("key1", {"data": "value"})
        
        assert cache.size() == 1
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("key1") is None
