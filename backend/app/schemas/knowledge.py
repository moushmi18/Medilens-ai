"""Knowledge source Pydantic schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class KnowledgeSourceResponse(BaseModel):
    """Response for a knowledge source."""
    
    id: UUID
    title: str
    publisher: str
    url: str
    topic: str | None = None
    content_hash: str | None = None
    verification_status: str
    is_active: bool
    retrieval_date: datetime
    created_at: datetime
    
    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def source_type(self) -> str:
        pub = (self.publisher or "").lower()
        if "medline" in pub:
            return "medlineplus"
        if "niddk" in pub or "nih" in pub:
            return "nih_niddk"
        if "nhs" in pub:
            return "nhs"
        if "who" in pub:
            return "who"
        return pub or "unknown"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def source_url(self) -> str:
        return self.url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def chunk_count(self) -> int:
        return 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_refreshed(self) -> datetime | None:
        return self.retrieval_date


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
