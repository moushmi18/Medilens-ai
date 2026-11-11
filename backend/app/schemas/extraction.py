"""Extraction Pydantic schemas."""
from uuid import UUID

from pydantic import BaseModel


class ExtractedResultResponse(BaseModel):
    """Response for a single extracted result."""
    
    id: UUID
    report_id: UUID
    test_name: str
    observed_value: str | None = None
    unit: str | None = None
    reference_range_low: str | None = None
    reference_range_high: str | None = None
    reference_range_text: str | None = None
    is_abnormal: bool | None = None
    page_number: int | None = None
    confidence_score: float | None = None
    needs_verification: bool = False
    verification_note: str | None = None
    
    model_config = {"from_attributes": True}


class ExtractedResultsResponse(BaseModel):
    """Response for multiple extracted results."""
    
    report_id: UUID
    results: list[ExtractedResultResponse]
    total: int


class VerifyResultRequest(BaseModel):
    """Request to verify an extracted result."""
    
    observed_value: str | None = None
    unit: str | None = None
    reference_range_low: str | None = None
    reference_range_high: str | None = None
    verification_note: str | None = None
