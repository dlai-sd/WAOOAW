"""
Vector Memory System using Pinecone

Provides semantic memory storage and recall for WAOOAW agents.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VectorMemory:
    """
    Vector memory system using Pinecone for semantic recall.
    
    Enables agents to:
    - Store memories with semantic embeddings
    - Recall similar past experiences
    - Learn from patterns across decisions
    """
    
    def __init__(self, api_key: str, index_name: str = "waooaw-memory"):
        """
        Initialize vector memory.
        
        Args:
            api_key: Pinecone API key
            index_name: Pinecone index name
        """
        self.api_key = api_key
        self.index_name = index_name
        self.index = None
        
        try:
            from pinecone import Pinecone
            
            pc = Pinecone(api_key=api_key)
            
            # Get or create index
            if index_name not in [idx.name for idx in pc.list_indexes()]:
                logger.warning(f"Index '{index_name}' not found. Please create it first.")
            else:
                self.index = pc.Index(index_name)
                logger.info(f"✅ Connected to Pinecone index: {index_name}")
                
        except ImportError:
            logger.warning("Pinecone library not installed. Vector memory disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
    
    def store_memory(self, key: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Store memory with semantic embedding.
        
        Args:
            key: Unique identifier for memory
            content: Text content to embed
            metadata: Additional metadata (agent_id, type, etc.)
        """
        if not self.index:
            logger.debug("Vector memory not available, skipping store")
            return
        
        try:
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Store in Pinecone
            from datetime import datetime
            
            self.index.upsert(vectors=[{
                'id': key,
                'values': embedding,
                'metadata': {
                    **metadata,
                    'content': content[:1000],  # Store preview
                    'stored_at': datetime.now().isoformat()
                }
            }])
            
            logger.debug(f"Stored memory: {key}")
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
    
    def recall_similar(self, query: str, top_k: int = 5, 
                      filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recall similar memories based on semantic similarity.
        
        Args:
            query: Text query to search for
            top_k: Number of results to return
            filter: Optional metadata filter
        
        Returns:
            List of similar memories with metadata and similarity scores
        """
        if not self.index:
            logger.debug("Vector memory not available, returning empty results")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
            
            # Format results
            memories = []
            for match in results.matches:
                memories.append({
                    'id': match.id,
                    'similarity': match.score,
                    'metadata': match.metadata
                })
            
            logger.debug(f"Recalled {len(memories)} similar memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI or fallback.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            # Try OpenAI embeddings (best quality)
            import openai
            import os
            
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.debug(f"OpenAI embedding failed, using fallback: {e}")
            
            # Fallback: Simple hash-based embedding (for testing)
            # In production, should use proper embedding model
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str, dimensions: int = 1536) -> List[float]:
        """
        Fallback embedding using simple hashing.
        
        NOT FOR PRODUCTION - only for testing when OpenAI is unavailable.
        """
        import hashlib
        
        # Generate deterministic vector from text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Expand to desired dimensions
        vector = []
        for i in range(dimensions):
            byte_idx = i % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] / 255.0) * 2 - 1)  # Normalize to [-1, 1]
        
        return vector
