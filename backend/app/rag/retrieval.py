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
            results = self.qdrant.search(
                collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
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
            results = self.qdrant.search(
                collection_name=USER_REPORTS_COLLECTION,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
            )
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
    
    def combined_search(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        knowledge_limit: int = 3,
        report_limit: int = 3,
        score_threshold: float = 0.5,
    ) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
        """Search both knowledge base and user reports.
        
        Args:
            query: Search query
            user_id: User ID for report isolation
            report_id: Optional specific report
            knowledge_limit: Max knowledge results
            report_limit: Max report results
            score_threshold: Minimum relevance score
            
        Returns:
            Tuple of (knowledge_chunks, report_chunks)
        """
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
