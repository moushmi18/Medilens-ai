"""Reports API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.schemas.reports import (
    ReportUploadResponse,
    ReportResponse,
    ReportStatusResponse,
    ReportListResponse,
)
from app.services.auth_service import AuthService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


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
