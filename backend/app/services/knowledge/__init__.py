"""
Knowledge Base Services

Provides RAG (Retrieval-Augmented Generation) capabilities:
- Document embedding and storage
- Semantic search with pgvector
- Knowledge retrieval for agent prompts
"""

from .document_store import DocumentStore, Document, DocumentMetadata
from .embeddings import EmbeddingService
from .rag_retriever import RAGRetriever, RetrievalResult

__all__ = [
    "DocumentStore",
    "Document",
    "DocumentMetadata",
    "EmbeddingService",
    "RAGRetriever",
    "RetrievalResult",
]
