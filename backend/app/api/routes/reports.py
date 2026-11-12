"""Reports API routes."""
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_qdrant
from app.core.exceptions import AuthenticationError, NotFoundError
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
from app.ingestion.docx_parser import extract_text_from_docx

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


_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "image": None,  # derived from extension
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/{report_id}/file")
def get_report_file(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> FileResponse:
    """Serve the original uploaded file (per-user authorization enforced)."""
    user = auth_service.get_current_user(token)
    report = report_service.get_report(user, report_id)

    path = Path(report.storage_path)
    if not path.exists():
        raise NotFoundError("Report file", str(report_id))

    media_type = _MEDIA_TYPES.get(report.file_type)
    if report.file_type == "image":
        ext = path.suffix.lower()
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(ext, "application/octet-stream")
    if media_type is None:
        media_type = "application/octet-stream"

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=report.original_filename,
        content_disposition_type="inline",
    )


@router.get("/{report_id}/text", response_class=PlainTextResponse)
def get_report_text(
    report_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    report_service: ReportService = Depends(get_report_service),
) -> PlainTextResponse:
    """Return extracted text preview (used for DOCX and fallback text view)."""
    user = auth_service.get_current_user(token)
    report = report_service.get_report(user, report_id)
    path = Path(report.storage_path)
    if not path.exists():
        raise NotFoundError("Report file", str(report_id))

    if report.file_type == "docx":
        extracted = extract_text_from_docx(path)
        return PlainTextResponse(extracted.get("text") or "(empty document)")

    if report.file_type == "pdf":
        from app.ingestion import extract_text_from_pdf
        extracted = extract_text_from_pdf(path)
        return PlainTextResponse(extracted.get("text") or "(no extractable text)")

    raise HTTPException(status_code=400, detail="Text preview only available for DOCX/PDF")


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
