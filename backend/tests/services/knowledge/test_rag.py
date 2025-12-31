"""
Quick tests for Document Store and RAG Retriever
"""

import pytest
from app.services.knowledge.document_store import (
    DocumentStore,
    Document,
    DocumentMetadata,
    Industry,
    DocumentType
)
from app.services.knowledge.embeddings import EmbeddingService
from app.services.knowledge.rag_retriever import RAGRetriever


class TestDocumentStore:
    """Test DocumentStore basic functionality"""
    
    @pytest.mark.asyncio
    async def test_add_and_get_document(self):
        """Test adding and retrieving document"""
        store = DocumentStore()
        
        doc = Document(
            id="test-1",
            title="Test Document",
            content="This is test content",
            embedding=[0.1] * 1536
        )
        
        doc_id = await store.add_document(doc)
        assert doc_id == "test-1"
        
        retrieved = await store.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.title == "Test Document"
    
    @pytest.mark.asyncio
    async def test_search_documents(self):
        """Test vector search"""
        store = DocumentStore()
        embedding_service = EmbeddingService()
        
        # Add documents
        doc1 = Document(
            id="doc1",
            title="Python Programming",
            content="Python is a programming language",
            embedding=(await embedding_service.embed_text("Python programming")).embedding
        )
        doc2 = Document(
            id="doc2",
            title="JavaScript Guide",
            content="JavaScript runs in browsers",
            embedding=(await embedding_service.embed_text("JavaScript web development")).embedding
        )
        
        await store.add_document(doc1)
        await store.add_document(doc2)
        
        # Search
        query_embedding = (await embedding_service.embed_text("Python coding")).embedding
        results = await store.search_documents(query_embedding, limit=2)
        
        assert len(results) > 0
        # Python doc should be more relevant
        assert results[0][0].title == "Python Programming"


class TestRAGRetriever:
    """Test RAG Retriever"""
    
    @pytest.mark.asyncio
    async def test_retrieve_documents(self):
        """Test retrieving relevant documents"""
        store = DocumentStore()
        embedding_service = EmbeddingService()
        retriever = RAGRetriever(store, embedding_service, top_k=2, min_similarity=0.5)
        
        # Add knowledge documents
        doc1 = Document(
            id="kb1",
            title="Content Marketing Best Practices",
            content="Always start with audience research. Create value-driven content.",
            embedding=(await embedding_service.embed_text("content marketing strategy audience")).embedding,
            metadata=DocumentMetadata(
                industry=Industry.MARKETING,
                document_type=DocumentType.BEST_PRACTICE
            )
        )
        
        await store.add_document(doc1)
        
        # Retrieve
        result = await retriever.retrieve("How to create marketing content?")
        
        assert len(result.documents) > 0
        assert result.context_text != ""
        assert "<knowledge>" in result.context_text
    
    @pytest.mark.asyncio
    async def test_enhance_prompt(self):
        """Test enhancing prompt with knowledge"""
        store = DocumentStore()
        embedding_service = EmbeddingService()
        retriever = RAGRetriever(store, embedding_service)
        
        # Add document
        doc = Document(
            id="guide1",
            title="Email Marketing Tips",
            content="Subject lines should be under 50 characters.",
            embedding=(await embedding_service.embed_text("email marketing")).embedding
        )
        await store.add_document(doc)
        
        # Enhance prompt
        base_prompt = "Write an email campaign."
        enhanced, retrieval = await retriever.enhance_prompt(
            base_prompt,
            "email marketing best practices"
        )
        
        assert "<knowledge>" in enhanced or len(retrieval.documents) == 0


pytest.main([__file__, "-v"])
