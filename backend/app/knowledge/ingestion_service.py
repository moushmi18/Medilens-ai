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
    """Service for ingesting knowledge from trusted sources."""
    
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
        
        chunks = self.chunker.chunk_text(content)
        
        if not chunks:
            logger.warning("no_chunks_generated", url=url)
            raise ValueError("Content produced no chunks for embedding")
        
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embeddings.embed_texts(chunk_texts)
        
        source = KnowledgeSource(
            source_type=source_type.value,
            source_url=url,
            title=title,
            content_hash=content_hash,
            chunk_count=len(chunks),
            last_refreshed=datetime.utcnow(),
        )
        self.db.add(source)
        self.db.flush()
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "source_id": str(source.id),
                        "source_type": source_type.value,
                        "source_url": url,
                        "title": title,
                        "chunk_index": i,
                        "chunk_text": chunk.text,
                        "word_count": chunk.word_count,
                        **(metadata or {}),
                    },
                )
            )
        
        self.qdrant.upsert(
            collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
            points=points,
        )
        
        self.db.commit()
        
        logger.info(
            "content_ingested",
            source_id=str(source.id),
            url=url,
            chunks=len(chunks),
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
            source_type: Filter by source type
            limit: Max results
            offset: Offset for pagination
            
        Returns:
            Tuple of (sources, total_count)
        """
        query = select(KnowledgeSource)
        
        if source_type:
            query = query.where(KnowledgeSource.source_type == source_type.value)
        
        count_query = select(KnowledgeSource.id)
        if source_type:
            count_query = count_query.where(
                KnowledgeSource.source_type == source_type.value
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
        
        source.last_refreshed = datetime.utcnow()
        self.db.commit()
        
        logger.info("source_refreshed", source_id=str(source_id))
        return source
