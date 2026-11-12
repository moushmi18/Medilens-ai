"""Retrieval service for RAG pipeline.

Handles vector search against Qdrant collections with proper user isolation.
"""
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.logging import get_logger
from app.embeddings.qdrant_client import (
    TRUSTED_KNOWLEDGE_COLLECTION,
    USER_REPORTS_COLLECTION,
)
from app.knowledge.embeddings import EmbeddingService

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk from vector search."""
    id: str
    text: str
    score: float
    source_type: str
    source_url: str | None = None
    title: str | None = None
    metadata: dict[str, Any] | None = None
    collection: str | None = None


class RetrievalService:
    """Service for retrieving relevant context from vector stores."""
    
    def __init__(self, qdrant: QdrantClient):
        self.qdrant = qdrant
        self.embeddings = EmbeddingService()
    
    def search_trusted_knowledge(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[RetrievedChunk]:
        """Search trusted knowledge base.
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum relevance score
            
        Returns:
            List of relevant chunks
        """
        query_vector = self.embeddings.embed_query(query)
        
        try:
            from qdrant_client.models import QueryRequest
            
            results = self.qdrant.query_points(
                collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            ).points
        except Exception as e:
            logger.error("trusted_knowledge_search_failed", error=str(e))
            return []
        
        chunks = []
        for result in results:
            payload = result.payload or {}
            chunks.append(RetrievedChunk(
                id=str(result.id),
                text=payload.get("chunk_text", ""),
                score=result.score,
                source_type=payload.get("source_type", "unknown"),
                source_url=payload.get("source_url"),
                title=payload.get("title"),
                metadata=payload,
                collection=TRUSTED_KNOWLEDGE_COLLECTION,
            ))
        
        logger.info(
            "trusted_knowledge_searched",
            query_length=len(query),
            results=len(chunks),
        )
        
        return chunks
    
    def search_user_reports(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[RetrievedChunk]:
        """Search user's reports with strict isolation.
        
        IMPORTANT: Always filters by user_id to ensure data isolation.
        
        Args:
            query: Search query
            user_id: User ID (REQUIRED for isolation)
            report_id: Optional specific report to search
            limit: Max results
            score_threshold: Minimum relevance score
            
        Returns:
            List of relevant chunks from user's reports
        """
        query_vector = self.embeddings.embed_query(query)
        
        must_conditions = [
            FieldCondition(
                key="user_id",
                match=MatchValue(value=str(user_id)),
            )
        ]
        
        if report_id:
            must_conditions.append(
                FieldCondition(
                    key="report_id",
                    match=MatchValue(value=str(report_id)),
                )
            )
        
        search_filter = Filter(must=must_conditions)
        
        try:
            results = self.qdrant.query_points(
                collection_name=USER_REPORTS_COLLECTION,
                query=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
            ).points
        except Exception as e:
            logger.error("user_reports_search_failed", error=str(e))
            return []
        
        chunks = []
        for result in results:
            payload = result.payload or {}
            chunks.append(RetrievedChunk(
                id=str(result.id),
                text=payload.get("chunk_text", ""),
                score=result.score,
                source_type="user_report",
                source_url=None,
                title=payload.get("report_filename"),
                metadata=payload,
                collection=USER_REPORTS_COLLECTION,
            ))
        
        logger.info(
            "user_reports_searched",
            user_id=str(user_id),
            report_id=str(report_id) if report_id else None,
            results=len(chunks),
        )
        
        return chunks
    
    def _fetch_knowledge_corpus(self, limit: int = 500) -> list[RetrievedChunk]:
        """Fetch knowledge chunks for BM25 indexing (payload scroll)."""
        try:
            points, _ = self.qdrant.scroll(
                collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            logger.error("knowledge_corpus_fetch_failed", error=str(e))
            return []
        
        chunks = []
        for point in points:
            payload = point.payload or {}
            chunks.append(RetrievedChunk(
                id=str(point.id),
                text=payload.get("chunk_text", ""),
                score=0.0,
                source_type=payload.get("source_type", "unknown"),
                source_url=payload.get("source_url"),
                title=payload.get("title"),
                metadata=payload,
                collection=TRUSTED_KNOWLEDGE_COLLECTION,
            ))
        return chunks
    
    def search_hybrid(
        self,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
        score_threshold: float = 0.0,
    ) -> list[RetrievedChunk]:
        """Hybrid retrieval: vector search + BM25 fused with RRF."""
        from app.rag.bm25 import BM25Index, BM25Document, reciprocal_rank_fusion
        
        vector_chunks = self.search_trusted_knowledge(
            query=query,
            limit=candidate_limit,
            score_threshold=score_threshold,
        )
        
        corpus = self._fetch_knowledge_corpus()
        if not corpus:
            return vector_chunks[:limit]
        
        bm25 = BM25Index()
        bm25.add_documents([
            BM25Document(id=c.id, text=c.text, metadata=c.metadata)
            for c in corpus
        ])
        bm25_hits = bm25.search(query, limit=candidate_limit)
        
        vector_ranking = [(c.id, c.score) for c in vector_chunks]
        bm25_ranking = [(doc.id, score) for doc, score in bm25_hits]
        fused = reciprocal_rank_fusion([vector_ranking, bm25_ranking])
        
        by_id = {c.id: c for c in corpus}
        for c in vector_chunks:
            by_id[c.id] = c
        
        results: list[RetrievedChunk] = []
        for doc_id, rrf_score in fused[:limit]:
            chunk = by_id.get(doc_id)
            if not chunk:
                continue
            results.append(RetrievedChunk(
                id=chunk.id,
                text=chunk.text,
                score=rrf_score,
                source_type=chunk.source_type,
                source_url=chunk.source_url,
                title=chunk.title,
                metadata=chunk.metadata,
                collection=chunk.collection,
            ))
        
        logger.info("hybrid_search_complete", query_length=len(query), results=len(results))
        return results
    
    def search_hybrid_rerank(
        self,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
    ) -> list[RetrievedChunk]:
        """Hybrid retrieval followed by cross-encoder reranking."""
        from app.rag.reranker import CrossEncoderReranker
        
        candidates = self.search_hybrid(
            query=query,
            limit=candidate_limit,
            candidate_limit=max(candidate_limit, 30),
        )
        if not candidates:
            return []
        
        reranker = CrossEncoderReranker()
        ranked = reranker.rerank(
            query=query,
            results=[
                (c.id, c.text, c.score, c.metadata)
                for c in candidates
            ],
            top_k=limit,
        )
        
        by_id = {c.id: c for c in candidates}
        results = []
        for r in ranked:
            chunk = by_id.get(r.id)
            if not chunk:
                continue
            results.append(RetrievedChunk(
                id=chunk.id,
                text=chunk.text,
                score=r.rerank_score,
                source_type=chunk.source_type,
                source_url=chunk.source_url,
                title=chunk.title,
                metadata=chunk.metadata,
                collection=chunk.collection,
            ))
        return results
    
    def search_context_aware(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        knowledge_limit: int = 5,
        report_limit: int = 3,
    ) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
        """Context-aware RAG: hybrid+rerank knowledge + user-isolated report search."""
        knowledge_chunks = self.search_hybrid_rerank(
            query=query,
            limit=knowledge_limit,
        )
        report_chunks = self.search_user_reports(
            query=query,
            user_id=user_id,
            report_id=report_id,
            limit=report_limit,
            score_threshold=0.3,
        )
        return knowledge_chunks, report_chunks
    
    def combined_search(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        knowledge_limit: int = 3,
        report_limit: int = 3,
        score_threshold: float = 0.5,
        method: str = "context_aware",
    ) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
        """Search both knowledge base and user reports.
        
        method:
          - basic: vector-only knowledge + report search
          - hybrid: vector+BM25 RRF knowledge
          - hybrid_rerank: hybrid + cross-encoder
          - context_aware: hybrid_rerank + report-scoped search (default)
        """
        if method == "basic":
            knowledge_chunks = self.search_trusted_knowledge(
                query=query,
                limit=knowledge_limit,
                score_threshold=score_threshold,
            )
            report_chunks = self.search_user_reports(
                query=query,
                user_id=user_id,
                report_id=report_id,
                limit=report_limit,
                score_threshold=score_threshold,
            )
            return knowledge_chunks, report_chunks
        
        if method == "hybrid":
            knowledge_chunks = self.search_hybrid(
                query=query,
                limit=knowledge_limit,
            )
            report_chunks = self.search_user_reports(
                query=query,
                user_id=user_id,
                report_id=report_id,
                limit=report_limit,
                score_threshold=score_threshold,
            )
            return knowledge_chunks, report_chunks
        
        if method == "hybrid_rerank":
            knowledge_chunks = self.search_hybrid_rerank(
                query=query,
                limit=knowledge_limit,
            )
            report_chunks = self.search_user_reports(
                query=query,
                user_id=user_id,
                report_id=report_id,
                limit=report_limit,
                score_threshold=score_threshold,
            )
            return knowledge_chunks, report_chunks
        
        return self.search_context_aware(
            query=query,
            user_id=user_id,
            report_id=report_id,
            knowledge_limit=knowledge_limit,
            report_limit=report_limit,
        )
