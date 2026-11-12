"""Report Pydantic schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReportUploadResponse(BaseModel):
    """Response for report upload."""
    
    id: UUID
    filename: str
    original_filename: str
    status: str


class ReportResponse(BaseModel):
    """Full report response."""
    
    id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    processing_error: str | None = None
    report_date: datetime | None = None
    lab_name: str | None = None
    patient_name: str | None = None
    page_count: int | None = None
    ocr_required: bool
    created_at: datetime
    updated_at: datetime
    uploaded_at: datetime | None = None
    
    model_config = {"from_attributes": True}
    
    def model_post_init(self, __context) -> None:
        if self.uploaded_at is None:
            object.__setattr__(self, "uploaded_at", self.created_at)


class ReportStatusResponse(BaseModel):
    """Report processing status."""
    
    status: str
    error: str | None = None


class ReportListResponse(BaseModel):
    """Paginated report list."""
    
    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
