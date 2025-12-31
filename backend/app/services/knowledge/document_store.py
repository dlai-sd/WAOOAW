"""
Document Store with Supabase pgvector

Stores knowledge documents with vector embeddings for semantic search.
Uses Supabase (PostgreSQL + pgvector extension) for scalable vector storage.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class Industry(str, Enum):
    """Industries for knowledge categorization"""
    MARKETING = "marketing"
    EDUCATION = "education"
    SALES = "sales"
    GENERAL = "general"


class DocumentType(str, Enum):
    """Types of knowledge documents"""
    BEST_PRACTICE = "best_practice"
    TEMPLATE = "template"
    EXAMPLE = "example"
    GUIDE = "guide"
    CASE_STUDY = "case_study"
    FAQ = "faq"


@dataclass
class DocumentMetadata:
    """Metadata for knowledge document"""
    industry: Industry
    document_type: DocumentType
    task_types: List[str] = field(default_factory=list)  # e.g., ["content_creation", "seo"]
    tags: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    quality_score: float = 0.0  # 0-1, based on usage/feedback
    last_updated: Optional[datetime] = None
    source: Optional[str] = None  # URL or reference
    author: Optional[str] = None


@dataclass
class Document:
    """Knowledge document with embedding"""
    id: str
    title: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[DocumentMetadata] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": {
                "industry": self.metadata.industry.value if self.metadata else None,
                "document_type": self.metadata.document_type.value if self.metadata else None,
                "task_types": self.metadata.task_types if self.metadata else [],
                "tags": self.metadata.tags if self.metadata else [],
                "difficulty": self.metadata.difficulty if self.metadata else "intermediate",
                "quality_score": self.metadata.quality_score if self.metadata else 0.0,
            } if self.metadata else {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DocumentStore:
    """
    Store for knowledge documents with vector search.
    
    Uses Supabase (PostgreSQL + pgvector):
    - Free tier: 500MB database, unlimited API requests
    - pgvector: Fast cosine similarity search
    - SQL: Standard PostgreSQL queries
    
    Schema:
        CREATE TABLE knowledge_documents (
            id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(1536),  -- pgvector extension
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX ON knowledge_documents USING ivfflat (embedding vector_cosine_ops);
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize document store.
        
        Args:
            supabase_client: Supabase client (optional, for testing)
        """
        self.client = supabase_client
        self._local_store: Dict[str, Document] = {}  # Fallback for testing
    
    async def add_document(self, document: Document) -> str:
        """
        Add document to store.
        
        Args:
            document: Document to add
            
        Returns:
            Document ID
        """
        if document.id is None or document.id == "":
            document.id = str(uuid.uuid4())
        
        if self.client:
            # Real Supabase insert
            await self.client.table("knowledge_documents").insert({
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "embedding": document.embedding,
                "metadata": document.to_dict()["metadata"],
                "created_at": document.created_at.isoformat() if document.created_at else None
            }).execute()
        else:
            # Local storage (testing)
            self._local_store[document.id] = document
        
        return document.id
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Bulk add documents.
        
        Args:
            documents: List of documents
            
        Returns:
            List of document IDs
        """
        ids = []
        for doc in documents:
            doc_id = await self.add_document(doc)
            ids.append(doc_id)
        return ids
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None
        """
        if self.client:
            result = await self.client.table("knowledge_documents").select("*").eq("id", document_id).single().execute()
            if result.data:
                return self._row_to_document(result.data)
            return None
        else:
            return self._local_store.get(document_id)
    
    async def search_documents(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Semantic search for documents using vector similarity.
        
        Args:
            query_embedding: Query vector (1536-dim)
            limit: Max results to return
            filters: Optional filters (industry, document_type, etc.)
            
        Returns:
            List of (Document, similarity_score) tuples, sorted by relevance
        """
        if self.client:
            # Real vector search using pgvector
            query = self.client.table("knowledge_documents").select("*")
            
            # Apply filters
            if filters:
                if "industry" in filters:
                    query = query.eq("metadata->>industry", filters["industry"])
                if "document_type" in filters:
                    query = query.eq("metadata->>document_type", filters["document_type"])
            
            # Vector similarity search (cosine similarity)
            # Note: Actual syntax depends on Supabase pgvector implementation
            # This is pseudocode - real implementation would use pgvector's operators
            result = await query.order(
                f"embedding <=> '[{','.join(map(str, query_embedding))}]'",
                desc=False  # Ascending distance = highest similarity
            ).limit(limit).execute()
            
            results = []
            for row in result.data:
                doc = self._row_to_document(row)
                # Calculate similarity (1 - distance for cosine)
                distance = self._calculate_distance(query_embedding, doc.embedding)
                similarity = 1 - distance
                results.append((doc, similarity))
            
            return results
        else:
            # Local search (testing)
            results = []
            for doc in self._local_store.values():
                if doc.embedding is None:
                    continue
                
                # Apply filters
                if filters:
                    if "industry" in filters and doc.metadata:
                        if doc.metadata.industry.value != filters["industry"]:
                            continue
                    if "document_type" in filters and doc.metadata:
                        if doc.metadata.document_type.value != filters["document_type"]:
                            continue
                
                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                results.append((doc, similarity))
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
    
    async def update_document(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update document fields.
        
        Args:
            document_id: Document ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        if self.client:
            await self.client.table("knowledge_documents").update(updates).eq("id", document_id).execute()
            return True
        else:
            if document_id in self._local_store:
                doc = self._local_store[document_id]
                for key, value in updates.items():
                    if hasattr(doc, key):
                        setattr(doc, key, value)
                return True
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        if self.client:
            await self.client.table("knowledge_documents").delete().eq("id", document_id).execute()
            return True
        else:
            if document_id in self._local_store:
                del self._local_store[document_id]
                return True
            return False
    
    async def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents with optional filters"""
        if self.client:
            query = self.client.table("knowledge_documents").select("count")
            if filters:
                if "industry" in filters:
                    query = query.eq("metadata->>industry", filters["industry"])
            result = await query.execute()
            return result.count
        else:
            if not filters:
                return len(self._local_store)
            
            count = 0
            for doc in self._local_store.values():
                if filters.get("industry") and doc.metadata:
                    if doc.metadata.industry.value == filters["industry"]:
                        count += 1
                else:
                    count += 1
            return count
    
    def _row_to_document(self, row: dict) -> Document:
        """Convert database row to Document"""
        metadata_dict = row.get("metadata", {})
        metadata = DocumentMetadata(
            industry=Industry(metadata_dict.get("industry", "general")),
            document_type=DocumentType(metadata_dict.get("document_type", "guide")),
            task_types=metadata_dict.get("task_types", []),
            tags=metadata_dict.get("tags", []),
            difficulty=metadata_dict.get("difficulty", "intermediate"),
            quality_score=metadata_dict.get("quality_score", 0.0)
        ) if metadata_dict else None
        
        return Document(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            embedding=row.get("embedding"),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
        )
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine distance (1 - similarity)"""
        return 1 - self._cosine_similarity(vec1, vec2)
