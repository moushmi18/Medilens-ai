"""Knowledge source Pydantic schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeSourceResponse(BaseModel):
    """Response for a knowledge source."""
    
    id: UUID
    source_type: str
    source_url: str
    title: str
    chunk_count: int
    last_refreshed: datetime | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class KnowledgeSourceListResponse(BaseModel):
    """Response for list of knowledge sources."""
    
    items: list[KnowledgeSourceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class IngestContentRequest(BaseModel):
    """Request to ingest content into knowledge base."""
    
    url: str
    source_type: str
    title: str
    content: str
    metadata: dict | None = None
