"""
ML Inference Client - calls ML Inference Service (port 8005) for embeddings

Architecture: Async httpx client with retry strategy + timeout <100ms SLA
Reference: PLANT_BLUEPRINT Section 9.5 (ML Inference Service)
"""

import httpx
import hashlib
from typing import List, Optional
import asyncio
import logging

from core.config import settings
from core.exceptions import PlantException


logger = logging.getLogger(__name__)


class MLInferenceClient:
    """
    Client for ML Inference Service.
    
    Responsibilities:
    - Generate embeddings (384-dim MiniLM)
    - Retry strategy (exponential backoff, 3 attempts)
    - Timeout enforcement (<100ms SLA)
    - Error handling + logging
    """
    
    def __init__(
        self,
        base_url: str = None,
        timeout_ms: int = None,
        max_retries: int = 3,
    ):
        self.base_url = base_url or settings.ml_service_url
        self.timeout_ms = timeout_ms or settings.ml_service_timeout_ms
        self.max_retries = max_retries
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_ms / 1000.0),
        )
    
    async def generate_embedding(
        self,
        text: str,
        model: str = None,
    ) -> List[float]:
        """
        Generate embedding for text using ML Inference Service.
        
        Args:
            text: Input text (skill description, industry context, etc.)
            model: Model name (default: MiniLM-384 from settings)
        
        Returns:
            Embedding vector (384 dimensions)
        
        Raises:
            PlantException: If inference fails after retries
        """
        model = model or settings.ml_model
        
        # Calculate content hash for caching
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        
        payload = {
            "text": text,
            "model": model,
            "content_hash": content_hash,
        }
        
        # Retry with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    "/generate-embedding",
                    json=payload,
                )
                response.raise_for_status()
                
                data = response.json()
                embedding = data.get("embedding")
                
                if not embedding or len(embedding) != settings.ml_embedding_dimension:
                    raise PlantException(
                        f"Invalid embedding: expected {settings.ml_embedding_dimension} dims, "
                        f"got {len(embedding) if embedding else 0}"
                    )
                
                logger.info(
                    f"Generated embedding (attempt {attempt + 1}): "
                    f"{content_hash[:8]}... -> {len(embedding)} dims"
                )
                
                return embedding
                
            except httpx.TimeoutException:
                logger.warning(
                    f"ML inference timeout (attempt {attempt + 1}/{self.max_retries}): "
                    f"{self.timeout_ms}ms exceeded"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise PlantException(
                        f"ML inference timeout after {self.max_retries} attempts"
                    )
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"ML inference HTTP error: {e.response.status_code} {e.response.text}")
                raise PlantException(f"ML inference failed: {e.response.text}")
                
            except Exception as e:
                logger.error(f"ML inference error: {str(e)}")
                raise PlantException(f"ML inference error: {str(e)}")
    
    async def batch_generate_embeddings(
        self,
        texts: List[str],
        model: str = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (parallel).
        
        Args:
            texts: List of input texts
            model: Model name
        
        Returns:
            List of embedding vectors
        """
        tasks = [self.generate_embedding(text, model) for text in texts]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_embeddings = []
        for i, embedding in enumerate(embeddings):
            if isinstance(embedding, Exception):
                logger.error(f"Failed to generate embedding for text {i}: {embedding}")
            else:
                valid_embeddings.append(embedding)
        
        return valid_embeddings
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
