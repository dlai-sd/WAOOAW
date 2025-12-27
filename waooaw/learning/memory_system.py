"""
Memory System - Story 4.1

Vector-based memory for agent learning and context retention.
Part of Epic 4: Learning & Memory.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import time
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    importance: float = 1.0  # 0.0 to 1.0


class MemorySystem:
    """
    Vector-based memory system for agent learning.
    
    Features:
    - Store experiences with metadata
    - Semantic search (similarity-based)
    - Importance scoring
    - Memory consolidation (merge similar memories)
    - Forgetting (LRU + importance-based)
    
    Memory Types:
    - Episodic: Specific events (PR reviews, decisions)
    - Semantic: General knowledge (coding patterns, policies)
    - Procedural: How to perform tasks
    """
    
    def __init__(
        self,
        max_memories: int = 1000,
        embedding_dim: int = 384,
        similarity_threshold: float = 0.8
    ):
        """
        Initialize memory system.
        
        Args:
            max_memories: Maximum memories to store
            embedding_dim: Embedding vector dimension
            similarity_threshold: Threshold for memory consolidation
        """
        self.max_memories = max_memories
        self.embedding_dim = embedding_dim
        self.similarity_threshold = similarity_threshold
        
        # Memory stores by type
        self.episodic_memories: Dict[str, MemoryEntry] = {}
        self.semantic_memories: Dict[str, MemoryEntry] = {}
        self.procedural_memories: Dict[str, MemoryEntry] = {}
        
        # Statistics
        self.total_stored = 0
        self.total_retrieved = 0
        self.consolidation_count = 0
        self.forgetting_count = 0
        
        logger.info(
            f"MemorySystem initialized: max={max_memories}, dim={embedding_dim}"
        )
    
    def store(
        self,
        content: str,
        memory_type: str = "episodic",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store a memory.
        
        Args:
            content: Memory content (text)
            memory_type: Type (episodic, semantic, procedural)
            metadata: Additional metadata
            importance: Importance score (0-1)
            embedding: Pre-computed embedding (optional)
            
        Returns:
            Memory ID
        """
        # Generate ID
        memory_id = f"{memory_type}_{int(time.time() * 1000)}_{self.total_stored}"
        
        # Create embedding if not provided
        if embedding is None:
            embedding = self._generate_embedding(content)
        
        # Create memory entry
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            importance=importance
        )
        
        # Store in appropriate memory type
        store = self._get_memory_store(memory_type)
        
        # Check capacity and consolidate if needed
        if len(store) >= self.max_memories:
            self._consolidate_or_forget(memory_type)
        
        store[memory_id] = entry
        self.total_stored += 1
        
        logger.info(
            f"Memory stored: {memory_id} (type={memory_type}, importance={importance:.2f})"
        )
        
        return memory_id
    
    def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Retrieve memories by semantic similarity.
        
        Args:
            query: Search query
            memory_type: Filter by type (None = all types)
            top_k: Number of results
            min_importance: Minimum importance threshold
            
        Returns:
            List of memory entries sorted by relevance
        """
        query_embedding = self._generate_embedding(query)
        
        # Collect all memories to search
        if memory_type:
            stores = [self._get_memory_store(memory_type)]
        else:
            stores = [
                self.episodic_memories,
                self.semantic_memories,
                self.procedural_memories
            ]
        
        candidates = []
        for store in stores:
            for entry in store.values():
                if entry.importance >= min_importance:
                    similarity = self._cosine_similarity(
                        query_embedding,
                        entry.embedding
                    )
                    candidates.append((similarity, entry))
        
        # Sort by similarity
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Update access statistics
        results = []
        for similarity, entry in candidates[:top_k]:
            entry.access_count += 1
            entry.last_accessed = time.time()
            results.append(entry)
        
        self.total_retrieved += len(results)
        
        logger.debug(
            f"Retrieved {len(results)} memories for query: '{query[:50]}...'"
        )
        
        return results
    
    def update_importance(self, memory_id: str, new_importance: float) -> None:
        """Update memory importance score."""
        for store in [
            self.episodic_memories,
            self.semantic_memories,
            self.procedural_memories
        ]:
            if memory_id in store:
                store[memory_id].importance = new_importance
                logger.debug(f"Updated importance: {memory_id} -> {new_importance}")
                return
        
        logger.warning(f"Memory not found: {memory_id}")
    
    def forget(self, memory_id: str) -> bool:
        """
        Forget a specific memory.
        
        Args:
            memory_id: Memory to forget
            
        Returns:
            True if forgotten, False if not found
        """
        for store in [
            self.episodic_memories,
            self.semantic_memories,
            self.procedural_memories
        ]:
            if memory_id in store:
                del store[memory_id]
                self.forgetting_count += 1
                logger.info(f"Memory forgotten: {memory_id}")
                return True
        
        return False
    
    def consolidate(self, memory_type: str = "episodic") -> int:
        """
        Consolidate similar memories.
        
        Finds similar memories and merges them into a single,
        more general memory with combined importance.
        
        Args:
            memory_type: Type of memories to consolidate
            
        Returns:
            Number of memories consolidated
        """
        store = self._get_memory_store(memory_type)
        memories = list(store.values())
        
        consolidated = 0
        to_remove = set()
        
        for i, mem1 in enumerate(memories):
            if mem1.id in to_remove:
                continue
            
            for mem2 in memories[i+1:]:
                if mem2.id in to_remove:
                    continue
                
                similarity = self._cosine_similarity(
                    mem1.embedding,
                    mem2.embedding
                )
                
                if similarity >= self.similarity_threshold:
                    # Merge memories
                    merged_content = self._merge_memories(mem1, mem2)
                    merged_importance = max(mem1.importance, mem2.importance)
                    
                    # Update first memory
                    mem1.content = merged_content
                    mem1.importance = merged_importance
                    mem1.access_count += mem2.access_count
                    
                    # Mark second for removal
                    to_remove.add(mem2.id)
                    consolidated += 1
                    self.consolidation_count += 1
        
        # Remove consolidated memories
        for memory_id in to_remove:
            del store[memory_id]
        
        logger.info(f"Consolidated {consolidated} memories (type={memory_type})")
        
        return consolidated
    
    def _consolidate_or_forget(self, memory_type: str) -> None:
        """Consolidate or forget memories when at capacity."""
        # Try consolidation first
        consolidated = self.consolidate(memory_type)
        
        if consolidated > 0:
            return
        
        # If consolidation didn't help, forget least important
        store = self._get_memory_store(memory_type)
        
        # Sort by importance * recency
        memories = sorted(
            store.values(),
            key=lambda m: m.importance * (1.0 / (time.time() - m.last_accessed + 1))
        )
        
        # Forget bottom 10%
        to_forget = max(1, len(memories) // 10)
        for entry in memories[:to_forget]:
            self.forget(entry.id)
    
    def _get_memory_store(self, memory_type: str) -> Dict[str, MemoryEntry]:
        """Get memory store by type."""
        stores = {
            "episodic": self.episodic_memories,
            "semantic": self.semantic_memories,
            "procedural": self.procedural_memories
        }
        return stores.get(memory_type, self.episodic_memories)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Placeholder: In production, use sentence-transformers or OpenAI embeddings.
        For now, use simple hash-based embedding.
        """
        # Simple hash-based embedding (deterministic)
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if len(embedding) >= self.embedding_dim:
                break
            val = int.from_bytes(hash_bytes[i:i+2], 'big') / 65535.0
            embedding.append(val)
        
        # Pad if needed
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        return embedding[:self.embedding_dim]
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _merge_memories(self, mem1: MemoryEntry, mem2: MemoryEntry) -> str:
        """Merge two similar memories into one."""
        # Simple concatenation for now
        return f"{mem1.content} | {mem2.content}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "episodic_count": len(self.episodic_memories),
            "semantic_count": len(self.semantic_memories),
            "procedural_count": len(self.procedural_memories),
            "total_count": (
                len(self.episodic_memories) +
                len(self.semantic_memories) +
                len(self.procedural_memories)
            ),
            "max_memories": self.max_memories,
            "total_stored": self.total_stored,
            "total_retrieved": self.total_retrieved,
            "consolidation_count": self.consolidation_count,
            "forgetting_count": self.forgetting_count
        }
    
    def export_memories(self, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export memories to JSON-serializable format."""
        stores = []
        if memory_type:
            stores = [self._get_memory_store(memory_type)]
        else:
            stores = [
                self.episodic_memories,
                self.semantic_memories,
                self.procedural_memories
            ]
        
        exported = []
        for store in stores:
            for entry in store.values():
                exported.append({
                    "id": entry.id,
                    "content": entry.content,
                    "metadata": entry.metadata,
                    "timestamp": entry.timestamp,
                    "importance": entry.importance,
                    "access_count": entry.access_count
                })
        
        return exported
