"""Reports API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_qdrant
from app.core.exceptions import AuthenticationError
from app.schemas.reports import (
    ReportUploadResponse,
    ReportResponse,
    ReportStatusResponse,
    ReportListResponse,
)
from app.schemas.extraction import (
    ExtractedResultResponse,
    ExtractedResultsResponse,
    VerifyResultRequest,
)
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/reports")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_report_service(
    db: Session = Depends(get_db),
    qdrant=Depends(get_qdrant),
) -> ReportService:
    return ReportService(db, qdrant=qdrant)


def get_extraction_service(
    db: Session = Depends(get_db),
    qdrant=Depends(get_qdrant),
) -> ExtractionService:
    return ExtractionService(db, qdrant=qdrant)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    """Extract token from Authorization header."""
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


@router.post("/upload", response_model=ReportUploadResponse, status_code=201)
async def upload_report(
    file: UploadFile = File(...),
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> ReportUploadResponse:
    """Upload a new medical report."""
    user = auth_service.get_current_user(token)
    
    report = report_service.upload_report(
        user=user,
        file=file.file,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )
    
    return ReportUploadResponse(
        id=report.id,
        filename=report.filename,
        original_filename=report.original_filename,
        status=report.status,
    )


@router.get("", response_model=ReportListResponse)
def list_reports(
    page: int = 1,
    page_size: int = 10,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    """List user's reports with pagination."""
    user = auth_service.get_current_user(token)
    reports, total = report_service.list_reports(user, page, page_size)
    
    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Get a specific report."""
    user = auth_service.get_current_user(token)
    report = report_service.get_report(user, report_id)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
def get_report_status(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> ReportStatusResponse:
    """Get report processing status."""
    user = auth_service.get_current_user(token)
    report = report_service.get_report(user, report_id)
    return ReportStatusResponse(
        status=report.status,
        error=report.processing_error,
    )


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> None:
    """Delete a report."""
    user = auth_service.get_current_user(token)
    report_service.delete_report(user, report_id)


@router.get("/{report_id}/results", response_model=ExtractedResultsResponse)
def get_report_results(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ExtractedResultsResponse:
    """Get extracted results for a report."""
    user = auth_service.get_current_user(token)
    results = extraction_service.get_results(user, report_id)
    
    return ExtractedResultsResponse(
        report_id=report_id,
        results=[ExtractedResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


@router.post("/{report_id}/process", response_model=ExtractedResultsResponse)
def process_report(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ExtractedResultsResponse:
    """Process a report to extract structured data."""
    user = auth_service.get_current_user(token)
    report_service.get_report(user, report_id)
    
    results = extraction_service.process_report(report_id)
    
    return ExtractedResultsResponse(
        report_id=report_id,
        results=[ExtractedResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


@router.patch("/{report_id}/results/{result_id}", response_model=ExtractedResultResponse)
def verify_result(
    report_id: UUID,
    result_id: UUID,
    request: VerifyResultRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ExtractedResultResponse:
    """Verify and update an extracted result."""
    user = auth_service.get_current_user(token)
    
    result = extraction_service.verify_result(
        user=user,
        result_id=result_id,
        observed_value=request.observed_value,
        unit=request.unit,
        reference_range_low=request.reference_range_low,
        reference_range_high=request.reference_range_high,
        verification_note=request.verification_note,
    )
    
    return ExtractedResultResponse.model_validate(result)
