"""Knowledge module - trusted knowledge base ingestion and management.

Only ingests from permitted sources:
- MedlinePlus (medlineplus.gov)
- NIH / NIDDK
- NHS (nhs.uk)
- WHO (who.int)
"""
from .embeddings import EmbeddingService
from .chunker import SemanticChunker

__all__ = ["EmbeddingService", "SemanticChunker"]
