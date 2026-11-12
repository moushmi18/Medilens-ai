"""Qdrant vector database client and collection management."""
from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

TRUSTED_KNOWLEDGE_COLLECTION = "trusted_knowledge"
USER_REPORTS_COLLECTION = "user_reports"
EMBEDDING_DIM = 384  # BGE-small-en-v1.5


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    api_key = settings.qdrant_api_key or None
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=api_key,
        https=False if not api_key else None,
        prefer_grpc=False,
        check_compatibility=False,
    )


def ensure_collections_exist(client: QdrantClient | None = None) -> None:
    """Ensure required Qdrant collections exist."""
    if client is None:
        client = get_qdrant_client()

    collections_to_create = [
        {
            "name": TRUSTED_KNOWLEDGE_COLLECTION,
            "vectors_config": qdrant_models.VectorParams(
                size=EMBEDDING_DIM,
                distance=qdrant_models.Distance.COSINE,
            ),
        },
        {
            "name": USER_REPORTS_COLLECTION,
            "vectors_config": qdrant_models.VectorParams(
                size=EMBEDDING_DIM,
                distance=qdrant_models.Distance.COSINE,
            ),
        },
    ]

    existing = {c.name for c in client.get_collections().collections}

    for collection in collections_to_create:
        if collection["name"] not in existing:
            logger.info("creating_qdrant_collection", collection=collection["name"])
            client.create_collection(
                collection_name=collection["name"],
                vectors_config=collection["vectors_config"],
            )
        else:
            logger.debug("qdrant_collection_exists", collection=collection["name"])


def search_trusted_knowledge(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 10,
    score_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """Search the trusted knowledge collection."""
    results = client.search(
        collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
    )
    return [
        {
            "id": str(r.id),
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]


def search_user_reports(
    client: QdrantClient,
    query_vector: list[float],
    user_id: UUID,
    report_id: UUID | None = None,
    limit: int = 10,
    score_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """Search user reports with mandatory user_id filter for isolation."""
    must_conditions = [
        qdrant_models.FieldCondition(
            key="user_id",
            match=qdrant_models.MatchValue(value=str(user_id)),
        )
    ]

    if report_id:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="report_id",
                match=qdrant_models.MatchValue(value=str(report_id)),
            )
        )

    results = client.search(
        collection_name=USER_REPORTS_COLLECTION,
        query_vector=query_vector,
        query_filter=qdrant_models.Filter(must=must_conditions),
        limit=limit,
        score_threshold=score_threshold,
    )
    return [
        {
            "id": str(r.id),
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]


def upsert_trusted_knowledge(
    client: QdrantClient,
    points: list[dict[str, Any]],
) -> None:
    """Upsert points to trusted knowledge collection."""
    qdrant_points = [
        qdrant_models.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p["payload"],
        )
        for p in points
    ]
    client.upsert(
        collection_name=TRUSTED_KNOWLEDGE_COLLECTION,
        points=qdrant_points,
    )


def upsert_user_report_chunks(
    client: QdrantClient,
    points: list[dict[str, Any]],
) -> None:
    """Upsert points to user reports collection."""
    qdrant_points = [
        qdrant_models.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p["payload"],
        )
        for p in points
    ]
    client.upsert(
        collection_name=USER_REPORTS_COLLECTION,
        points=qdrant_points,
    )


def delete_user_report_vectors(
    client: QdrantClient,
    user_id: UUID,
    report_id: UUID,
) -> None:
    """Delete all vectors for a specific report (for privacy deletion)."""
    client.delete(
        collection_name=USER_REPORTS_COLLECTION,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id",
                        match=qdrant_models.MatchValue(value=str(user_id)),
                    ),
                    qdrant_models.FieldCondition(
                        key="report_id",
                        match=qdrant_models.MatchValue(value=str(report_id)),
                    ),
                ]
            )
        ),
    )
