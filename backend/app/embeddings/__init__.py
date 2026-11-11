"""Embeddings module - text embedding generation and management."""
from .qdrant_client import (
    get_qdrant_client,
    ensure_collections_exist,
    search_trusted_knowledge,
    search_user_reports,
    upsert_trusted_knowledge,
    upsert_user_report_chunks,
    delete_user_report_vectors,
    TRUSTED_KNOWLEDGE_COLLECTION,
    USER_REPORTS_COLLECTION,
    EMBEDDING_DIM,
)

__all__ = [
    "get_qdrant_client",
    "ensure_collections_exist",
    "search_trusted_knowledge",
    "search_user_reports",
    "upsert_trusted_knowledge",
    "upsert_user_report_chunks",
    "delete_user_report_vectors",
    "TRUSTED_KNOWLEDGE_COLLECTION",
    "USER_REPORTS_COLLECTION",
    "EMBEDDING_DIM",
]
