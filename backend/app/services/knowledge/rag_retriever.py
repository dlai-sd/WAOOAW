"""
RAG (Retrieval-Augmented Generation) Retriever

Combines document retrieval with prompt enhancement for agents.
Retrieves relevant knowledge documents and injects them into prompts.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from app.services.knowledge.document_store import DocumentStore, Document, Industry, DocumentType
from app.services.knowledge.embeddings import EmbeddingService


@dataclass
class RetrievalResult:
    """Result of RAG retrieval"""
    query: str
    documents: List[Document]
    similarities: List[float]
    context_text: str  # Formatted context for prompt injection
    total_tokens: int  # Approximate tokens in context
    
    def get_top_n(self, n: int) -> List[tuple[Document, float]]:
        """Get top N documents with scores"""
        return list(zip(self.documents[:n], self.similarities[:n]))


class RAGRetriever:
    """
    RAG retriever for knowledge-enhanced agent prompts.
    
    Process:
    1. Embed user query
    2. Search document store for relevant knowledge
    3. Rank results by relevance
    4. Format context for prompt injection
    5. Return enhanced prompt
    
    Features:
    - Top-k retrieval (default: 3 documents)
    - Relevance filtering (min similarity threshold)
    - Context formatting (numbered list, citations)
    - Token budget management
    """
    
    def __init__(
        self,
        document_store: DocumentStore,
        embedding_service: EmbeddingService,
        top_k: int = 3,
        min_similarity: float = 0.7,
        max_context_tokens: int = 2000
    ):
        """
        Initialize RAG retriever.
        
        Args:
            document_store: Document storage with vector search
            embedding_service: Service for embedding queries
            top_k: Number of documents to retrieve (default: 3)
            min_similarity: Minimum similarity score (0-1, default: 0.7)
            max_context_tokens: Max tokens for context (default: 2000)
        """
        self.document_store = document_store
        self.embedding_service = embedding_service
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.max_context_tokens = max_context_tokens
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: User query or task description
            filters: Optional filters (industry, document_type, etc.)
            top_k: Override default top_k
            
        Returns:
            RetrievalResult with documents and formatted context
        """
        k = top_k if top_k is not None else self.top_k
        
        # Embed query
        query_result = await self.embedding_service.embed_text(query)
        query_embedding = query_result.embedding
        
        # Search documents
        search_results = await self.document_store.search_documents(
            query_embedding=query_embedding,
            limit=k * 2,  # Retrieve more, then filter
            filters=filters
        )
        
        # Filter by similarity threshold
        filtered_results = [
            (doc, score) for doc, score in search_results
            if score >= self.min_similarity
        ]
        
        # Take top-k
        top_results = filtered_results[:k]
        
        if not top_results:
            # No relevant documents found
            return RetrievalResult(
                query=query,
                documents=[],
                similarities=[],
                context_text="",
                total_tokens=0
            )
        
        # Extract documents and scores
        documents = [doc for doc, _ in top_results]
        similarities = [score for _, score in top_results]
        
        # Format context
        context_text = self._format_context(documents, similarities)
        
        # Estimate tokens (rough: 4 chars per token)
        total_tokens = len(context_text) // 4
        
        # Truncate if exceeds max
        if total_tokens > self.max_context_tokens:
            context_text = self._truncate_context(context_text, self.max_context_tokens)
            total_tokens = self.max_context_tokens
        
        return RetrievalResult(
            query=query,
            documents=documents,
            similarities=similarities,
            context_text=context_text,
            total_tokens=total_tokens
        )
    
    async def enhance_prompt(
        self,
        base_prompt: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[str, RetrievalResult]:
        """
        Enhance prompt with retrieved knowledge.
        
        Args:
            base_prompt: Original agent prompt
            query: Query for retrieval
            filters: Optional filters
            
        Returns:
            Tuple of (enhanced_prompt, retrieval_result)
        """
        # Retrieve relevant knowledge
        retrieval = await self.retrieve(query, filters)
        
        if not retrieval.documents:
            # No knowledge found, return original prompt
            return base_prompt, retrieval
        
        # Inject knowledge into prompt
        enhanced_prompt = self._inject_context(base_prompt, retrieval.context_text)
        
        return enhanced_prompt, retrieval
    
    def _format_context(
        self,
        documents: List[Document],
        similarities: List[float]
    ) -> str:
        """
        Format retrieved documents as context text.
        
        Format:
        <knowledge>
        Here is relevant knowledge to help you:
        
        [1] Title (relevance: 95%)
        Content...
        
        [2] Title (relevance: 87%)
        Content...
        </knowledge>
        """
        lines = ["<knowledge>", "Here is relevant knowledge to help you:", ""]
        
        for i, (doc, score) in enumerate(zip(documents, similarities), 1):
            lines.append(f"[{i}] {doc.title} (relevance: {score:.0%})")
            lines.append(doc.content)
            lines.append("")  # Blank line between documents
        
        lines.append("</knowledge>")
        
        return "\n".join(lines)
    
    def _inject_context(self, base_prompt: str, context: str) -> str:
        """
        Inject context into base prompt.
        
        Inserts context after system prompt but before task.
        """
        # Simple injection: add context before task
        if "<task>" in base_prompt:
            parts = base_prompt.split("<task>")
            return f"{parts[0]}\n{context}\n<task>{parts[1]}"
        else:
            # No task marker, append to end
            return f"{base_prompt}\n\n{context}"
    
    def _truncate_context(self, context: str, max_tokens: int) -> str:
        """
        Truncate context to fit token budget.
        
        Keeps complete documents (doesn't cut mid-document).
        """
        # Split by document boundaries
        parts = context.split("\n\n")
        
        truncated_parts = ["<knowledge>", "Here is relevant knowledge to help you:", ""]
        current_tokens = 20  # Starting overhead
        
        for part in parts[3:]:  # Skip header
            part_tokens = len(part) // 4
            if current_tokens + part_tokens <= max_tokens:
                truncated_parts.append(part)
                current_tokens += part_tokens
            else:
                break
        
        truncated_parts.append("</knowledge>")
        
        return "\n\n".join(truncated_parts)
    
    async def retrieve_by_task_type(
        self,
        task_type: str,
        industry: Industry,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve documents for specific task type and industry.
        
        Args:
            task_type: Task type (e.g., "content_creation")
            industry: Industry filter
            top_k: Override default top_k
            
        Returns:
            RetrievalResult with matching documents
        """
        # Build query from task type
        query = f"{task_type} best practices for {industry.value}"
        
        # Add task_type to filters
        filters = {
            "industry": industry.value,
            # Note: task_types filtering would need custom SQL in real implementation
        }
        
        return await self.retrieve(query, filters=filters, top_k=top_k)
    
    async def retrieve_similar_examples(
        self,
        example_query: str,
        industry: Industry,
        limit: int = 5
    ) -> List[Document]:
        """
        Retrieve similar examples for learning.
        
        Args:
            example_query: Description of desired examples
            industry: Industry filter
            limit: Number of examples to retrieve
            
        Returns:
            List of example documents
        """
        filters = {
            "industry": industry.value,
            "document_type": DocumentType.EXAMPLE.value
        }
        
        retrieval = await self.retrieve(
            query=example_query,
            filters=filters,
            top_k=limit
        )
        
        return retrieval.documents
    
    def get_stats(self) -> dict:
        """Get retrieval statistics"""
        embedding_stats = self.embedding_service.get_stats()
        
        return {
            "top_k": self.top_k,
            "min_similarity": self.min_similarity,
            "max_context_tokens": self.max_context_tokens,
            "embedding_stats": embedding_stats
        }


class HybridRetriever(RAGRetriever):
    """
    Hybrid retriever combining vector search + keyword search.
    
    Uses both semantic similarity and keyword matching for better recall.
    """
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Hybrid retrieval: vector + keyword.
        
        1. Vector search (semantic)
        2. Keyword search (exact matching)
        3. Merge and re-rank results
        """
        # Get vector results
        vector_results = await super().retrieve(query, filters, top_k)
        
        # TODO: Add keyword search
        # For now, just return vector results
        return vector_results


class ReRanker:
    """
    Re-rank retrieved documents using additional signals.
    
    Signals:
    - Quality score (from metadata)
    - Recency (newer = better)
    - Usage statistics (popular = better)
    """
    
    def rerank(
        self,
        documents: List[Document],
        similarities: List[float],
        weights: Optional[Dict[str, float]] = None
    ) -> List[tuple[Document, float]]:
        """
        Re-rank documents using multiple signals.
        
        Args:
            documents: Retrieved documents
            similarities: Original similarity scores
            weights: Weights for signals (default: equal)
            
        Returns:
            Re-ranked list of (document, final_score) tuples
        """
        if weights is None:
            weights = {
                "similarity": 0.7,
                "quality": 0.2,
                "recency": 0.1
            }
        
        scored_docs = []
        
        for doc, sim in zip(documents, similarities):
            # Similarity score
            score = sim * weights["similarity"]
            
            # Quality score
            if doc.metadata and doc.metadata.quality_score > 0:
                score += doc.metadata.quality_score * weights["quality"]
            
            # Recency score (documents from last 30 days get boost)
            # Simplified: assume all docs are recent for now
            score += 0.5 * weights["recency"]
            
            scored_docs.append((doc, score))
        
        # Sort by final score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs
