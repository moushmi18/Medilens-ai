"""RAG pipeline implementation.

Implements the core RAG workflow:
1. Process query
2. Retrieve relevant context (knowledge + user reports)
3. Check evidence sufficiency
4. Generate response with LLM
5. Format with citations
"""
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional
from uuid import UUID

from qdrant_client import QdrantClient

from app.core.logging import get_logger
from app.llm import LLMProvider, get_llm_provider
from app.llm.provider import LLMMessage
from app.rag.retrieval import RetrievalService, RetrievedChunk
from app.rag.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    INSUFFICIENT_EVIDENCE_RESPONSE,
    EMERGENCY_KEYWORDS,
    EMERGENCY_RESPONSE,
)

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    citations: list[dict[str, Any]]
    knowledge_chunks: list[RetrievedChunk]
    report_chunks: list[RetrievedChunk]
    is_emergency: bool = False
    insufficient_evidence: bool = False


class RAGPipeline:
    """RAG pipeline for answering medical report questions."""
    
    def __init__(
        self,
        qdrant: QdrantClient,
        llm_provider: LLMProvider | None = None,
    ):
        self.retrieval = RetrievalService(qdrant)
        self.llm = llm_provider or get_llm_provider()
    
    def check_emergency(self, query: str) -> bool:
        """Check if query indicates an emergency."""
        query_lower = query.lower()
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in query_lower:
                return True
        return False
    
    def build_context(
        self,
        knowledge_chunks: list[RetrievedChunk],
        report_chunks: list[RetrievedChunk],
    ) -> tuple[str, str]:
        """Build context strings from retrieved chunks."""
        if knowledge_chunks:
            knowledge_context = "\n\n".join([
                f"[Source: {chunk.title or chunk.source_type}]\n{chunk.text}"
                for chunk in knowledge_chunks
            ])
        else:
            knowledge_context = "No relevant trusted knowledge found."
        
        if report_chunks:
            report_context = "\n\n".join([
                f"[From Report: {chunk.title or 'Unknown'}]\n{chunk.text}"
                for chunk in report_chunks
            ])
        else:
            report_context = "No specific report content relevant to this question."
        
        return knowledge_context, report_context
    
    def check_evidence_sufficiency(
        self,
        knowledge_chunks: list[RetrievedChunk],
        report_chunks: list[RetrievedChunk],
        min_score: float = 0.5,
    ) -> bool:
        """Check if retrieved evidence is sufficient to answer."""
        if not knowledge_chunks and not report_chunks:
            return False
        
        all_chunks = knowledge_chunks + report_chunks
        max_score = max(chunk.score for chunk in all_chunks)
        
        return max_score >= min_score
    
    def extract_citations(
        self,
        knowledge_chunks: list[RetrievedChunk],
    ) -> list[dict[str, Any]]:
        """Extract citation information from knowledge chunks."""
        citations = []
        seen_urls = set()
        
        for chunk in knowledge_chunks:
            if chunk.source_url and chunk.source_url not in seen_urls:
                citations.append({
                    "title": chunk.title or chunk.source_type,
                    "url": chunk.source_url,
                    "source_type": chunk.source_type,
                })
                seen_urls.add(chunk.source_url)
        
        return citations
    
    async def answer(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        temperature: float = 0.3,
    ) -> RAGResponse:
        """Generate an answer using RAG.
        
        Args:
            query: User's question
            user_id: User ID for report isolation
            report_id: Optional specific report to consider
            temperature: LLM temperature (lower = more focused)
            
        Returns:
            RAGResponse with answer and metadata
        """
        if self.check_emergency(query):
            logger.warning("emergency_query_detected", user_id=str(user_id))
            return RAGResponse(
                answer=EMERGENCY_RESPONSE,
                citations=[],
                knowledge_chunks=[],
                report_chunks=[],
                is_emergency=True,
            )
        
        knowledge_chunks, report_chunks = self.retrieval.combined_search(
            query=query,
            user_id=user_id,
            report_id=report_id,
            knowledge_limit=5,
            report_limit=3,
        )
        
        if not self.check_evidence_sufficiency(knowledge_chunks, report_chunks):
            logger.info("insufficient_evidence", user_id=str(user_id), query=query[:50])
            return RAGResponse(
                answer=INSUFFICIENT_EVIDENCE_RESPONSE,
                citations=[],
                knowledge_chunks=knowledge_chunks,
                report_chunks=report_chunks,
                insufficient_evidence=True,
            )
        
        knowledge_context, report_context = self.build_context(
            knowledge_chunks, report_chunks
        )
        
        user_prompt = RAG_PROMPT_TEMPLATE.format(
            knowledge_context=knowledge_context,
            report_context=report_context,
            question=query,
        )
        
        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]
        
        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        
        citations = self.extract_citations(knowledge_chunks)
        
        logger.info(
            "rag_response_generated",
            user_id=str(user_id),
            knowledge_chunks=len(knowledge_chunks),
            report_chunks=len(report_chunks),
            citations=len(citations),
        )
        
        return RAGResponse(
            answer=response.content,
            citations=citations,
            knowledge_chunks=knowledge_chunks,
            report_chunks=report_chunks,
        )
    
    async def answer_stream(
        self,
        query: str,
        user_id: UUID,
        report_id: UUID | None = None,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Stream an answer using RAG.
        
        Yields chunks of the response as they're generated.
        """
        if self.check_emergency(query):
            yield EMERGENCY_RESPONSE
            return
        
        knowledge_chunks, report_chunks = self.retrieval.combined_search(
            query=query,
            user_id=user_id,
            report_id=report_id,
        )
        
        if not self.check_evidence_sufficiency(knowledge_chunks, report_chunks):
            yield INSUFFICIENT_EVIDENCE_RESPONSE
            return
        
        knowledge_context, report_context = self.build_context(
            knowledge_chunks, report_chunks
        )
        
        user_prompt = RAG_PROMPT_TEMPLATE.format(
            knowledge_context=knowledge_context,
            report_context=report_context,
            question=query,
        )
        
        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]
        
        async for chunk in self.llm.generate_stream(
            messages=messages,
            temperature=temperature,
        ):
            yield chunk
