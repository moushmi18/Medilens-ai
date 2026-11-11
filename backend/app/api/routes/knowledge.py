"""Knowledge source API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_qdrant
from app.knowledge.ingestion_service import KnowledgeIngestionService
from app.knowledge.sources import SourceType
from app.schemas.knowledge import (
    KnowledgeSourceResponse,
    KnowledgeSourceListResponse,
    IngestContentRequest,
)

router = APIRouter(prefix="/sources")


def get_ingestion_service(
    db: Session = Depends(get_db),
    qdrant = Depends(get_qdrant),
) -> KnowledgeIngestionService:
    return KnowledgeIngestionService(db, qdrant)


@router.get("", response_model=KnowledgeSourceListResponse)
def list_sources(
    page: int = 1,
    page_size: int = 20,
    source_type: str | None = None,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> KnowledgeSourceListResponse:
    """List knowledge sources."""
    st = None
    if source_type:
        try:
            st = SourceType(source_type)
        except ValueError:
            raise HTTPException(400, f"Invalid source_type: {source_type}")
    
    offset = (page - 1) * page_size
    sources, total = service.list_sources(
        source_type=st,
        limit=page_size,
        offset=offset,
    )
    
    return KnowledgeSourceListResponse(
        items=[KnowledgeSourceResponse.model_validate(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{source_id}", response_model=KnowledgeSourceResponse)
def get_source(
    source_id: UUID,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> KnowledgeSourceResponse:
    """Get a knowledge source by ID."""
    source = service.get_source(source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    return KnowledgeSourceResponse.model_validate(source)


@router.post("", response_model=KnowledgeSourceResponse, status_code=201)
def ingest_content(
    request: IngestContentRequest,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> KnowledgeSourceResponse:
    """Ingest content into the knowledge base.
    
    Note: This endpoint is for admin/internal use only.
    In production, this should be protected.
    """
    try:
        source_type = SourceType(request.source_type)
    except ValueError:
        raise HTTPException(400, f"Invalid source_type: {request.source_type}")
    
    try:
        source = service.ingest_content(
            url=request.url,
            source_type=source_type,
            title=request.title,
            content=request.content,
            metadata=request.metadata,
        )
        return KnowledgeSourceResponse.model_validate(source)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{source_id}/refresh", response_model=KnowledgeSourceResponse)
def refresh_source(
    source_id: UUID,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> KnowledgeSourceResponse:
    """Refresh a knowledge source."""
    source = service.refresh_source(source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    return KnowledgeSourceResponse.model_validate(source)
