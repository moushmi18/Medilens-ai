"""Knowledge ingestion service.

Handles ingesting content from permitted sources into Qdrant.
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.core.logging import get_logger
from app.database.models import KnowledgeSource
from app.embeddings.qdrant_client import TRUSTED_KNOWLEDGE_COLLECTION
from app.knowledge.chunker import SemanticChunker
from app.knowledge.embeddings import EmbeddingService
from app.knowledge.sources import (
    SourceType,
    FetchedContent,
    KnowledgeFetcher,
    generate_content_hash,
)

logger = get_logger(__name__)


class KnowledgeIngestionService:
    """Service for ingesting knowledge from trusted sources.
    
    Uses LlamaIndex SentenceSplitter for semantic chunking when available,
    with the custom SemanticChunker as fallback. Custom hybrid retrieval
    (BM25 + RRF + rerank) remains in the RAG layer.
    """
    
    def __init__(
        self,
        db: Session,
        qdrant: QdrantClient,
    ):
        self.db = db
        self.qdrant = qdrant
        self.chunker = SemanticChunker()
        self.embeddings = EmbeddingService()
        self.fetcher = KnowledgeFetcher()
        self._llama_processor = None
    
    def _get_llama_processor(self):
        if self._llama_processor is None:
            try:
                from app.knowledge.llama_integration import LlamaIndexDocumentProcessor
                self._llama_processor = LlamaIndexDocumentProcessor(
                    chunk_size=512,
                    chunk_overlap=64,
                )
            except Exception as e:
                logger.warning("llamaindex_unavailable", error=str(e))
                self._llama_processor = False
        return self._llama_processor if self._llama_processor is not False else None
    
    def ingest_content(
        self,
        url: str,
        source_type: SourceType,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeSource:
        """Ingest content into the knowledge base.
        
        Args:
            url: Source URL
            source_type: Type of source
            title: Content title
            content: Raw content text
            metadata: Optional additional metadata
            
        Returns:
            Created KnowledgeSource record
        """
        content_hash = generate_content_hash(content)
        
        existing = self.db.execute(
            select(KnowledgeSource).where(
                KnowledgeSource.content_hash == content_hash
            )
        ).scalar_one_or_none()
        
        if existing:
            logger.info(
                "content_already_ingested",
                url=url,
                existing_id=str(existing.id),
            )
            return existing
        
        publisher_map = {
            SourceType.MEDLINEPLUS: "MedlinePlus / NLM",
            SourceType.NIH_NIDDK: "NIH / NIDDK",
            SourceType.NHS: "NHS",
            SourceType.WHO: "WHO",
        }
        topics = (metadata or {}).get("topics")
        topic_str = ", ".join(topics) if isinstance(topics, list) else (metadata or {}).get("topic")

        source = KnowledgeSource(
            title=title,
            publisher=publisher_map.get(source_type, source_type.value),
            url=url,
            retrieval_date=datetime.utcnow(),
            topic=topic_str,
            content_hash=content_hash,
            verification_status="verified",
            is_active=True,
        )
        self.db.add(source)
        self.db.flush()
        
        payload_meta = {
            "source_type": source_type.value,
            "source_url": url,
            "title": title,
            "publisher": source.publisher,
            **(metadata or {}),
        }
        
        chunk_count = 0
        llama = self._get_llama_processor()
        if llama is not None:
            chunk_count = llama.ingest_to_qdrant(
                client=self.qdrant,
                collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
                text=content,
                source_id=str(source.id),
                metadata=payload_meta,
            )
            if chunk_count == 0:
                raise ValueError("Content produced no chunks for embedding")
            logger.info("content_ingested_via_llamaindex", source_id=str(source.id), chunks=chunk_count)
        else:
            chunks = self.chunker.chunk_text(content)
            if not chunks:
                logger.warning("no_chunks_generated", url=url)
                raise ValueError("Content produced no chunks for embedding")
            
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embeddings.embed_texts(chunk_texts)
            
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid4())
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "source_id": str(source.id),
                            "chunk_index": i,
                            "chunk_text": chunk.text,
                            "word_count": chunk.word_count,
                            **payload_meta,
                        },
                    )
                )
            
            self.qdrant.upsert(
                collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
                points=points,
            )
            chunk_count = len(chunks)
            logger.info("content_ingested_via_fallback_chunker", source_id=str(source.id), chunks=chunk_count)
        
        self.db.commit()
        
        logger.info(
            "content_ingested",
            source_id=str(source.id),
            url=url,
            chunks=chunk_count,
        )
        
        return source
    
    def ingest_fetched_content(self, content: FetchedContent) -> KnowledgeSource:
        """Ingest fetched content into the knowledge base."""
        return self.ingest_content(
            url=content.url,
            source_type=content.source_type,
            title=content.title,
            content=content.content,
            metadata=content.metadata,
        )
    
    def list_sources(
        self,
        source_type: SourceType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[KnowledgeSource], int]:
        """List knowledge sources.
        
        Args:
            source_type: Optional publisher/type filter (matched against publisher text)
            limit: Max results
            offset: Offset for pagination
            
        Returns:
            Tuple of (sources, total_count)
        """
        query = select(KnowledgeSource).where(KnowledgeSource.is_active.is_(True))
        
        if source_type:
            query = query.where(KnowledgeSource.publisher.ilike(f"%{source_type.value}%"))
        
        count_query = select(KnowledgeSource.id).where(KnowledgeSource.is_active.is_(True))
        if source_type:
            count_query = count_query.where(
                KnowledgeSource.publisher.ilike(f"%{source_type.value}%")
            )
        total = len(self.db.execute(count_query).scalars().all())
        
        query = query.offset(offset).limit(limit)
        sources = list(self.db.execute(query).scalars().all())
        
        return sources, total
    
    def get_source(self, source_id: UUID) -> KnowledgeSource | None:
        """Get a knowledge source by ID."""
        return self.db.execute(
            select(KnowledgeSource).where(KnowledgeSource.id == source_id)
        ).scalar_one_or_none()
    
    def refresh_source(self, source_id: UUID) -> KnowledgeSource | None:
        """Refresh a source by re-fetching and re-embedding.
        
        Note: This is a placeholder - actual refresh logic depends
        on source type and would need to re-fetch from URL.
        """
        source = self.get_source(source_id)
        if not source:
            return None
        
        source.retrieval_date = datetime.utcnow()
        self.db.commit()
        
        logger.info("source_refreshed", source_id=str(source_id))
        return source
