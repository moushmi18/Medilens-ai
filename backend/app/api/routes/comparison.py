"""Comparison and summary API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.schemas.comparison import (
    CompareRequest,
    ComparisonResponse,
    TestComparison,
    ReportValue,
    SummaryRequest,
)
from app.services.auth_service import AuthService
from app.services.comparison_service import ComparisonService
from app.services.summary_service import SummaryService

reports_router = APIRouter(prefix="/reports")
router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_comparison_service(db: Session = Depends(get_db)) -> ComparisonService:
    return ComparisonService(db)


def get_summary_service(db: Session = Depends(get_db)) -> SummaryService:
    return SummaryService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


@reports_router.post("/compare", response_model=ComparisonResponse)
def compare_reports(
    request: CompareRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonResponse:
    """Compare extracted results across multiple reports."""
    user = auth_service.get_current_user(token)
    
    result = comparison_service.compare_reports(
        user=user,
        report_ids=request.report_ids,
    )
    
    return ComparisonResponse(
        report_ids=result.report_ids,
        report_dates=result.report_dates,
        comparisons=[
            TestComparison(
                test_name=c.test_name,
                reports=[ReportValue(**r) for r in c.reports],
                change=c.change,
                change_direction=c.change_direction,
                unit=c.unit,
            )
            for c in result.comparisons
        ],
        matched_tests=result.matched_tests,
        unmatched_tests=result.unmatched_tests,
    )


@reports_router.post("/{report_id}/summary")
def generate_summary(
    report_id: UUID,
    request: SummaryRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    summary_service: SummaryService = Depends(get_summary_service),
) -> StreamingResponse:
    """Generate a doctor summary PDF for a report."""
    user = auth_service.get_current_user(token)
    
    pdf_content, filename = summary_service.generate_summary(
        user=user,
        report_id=report_id,
        include_questions=request.include_questions,
    )
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


class DoctorSummaryBody(SummaryRequest):
    report_id: UUID | None = None


@router.post("/doctor-summary")
def generate_doctor_summary(
    request: DoctorSummaryBody,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    summary_service: SummaryService = Depends(get_summary_service),
) -> StreamingResponse:
    """Spec alias: POST /api/doctor-summary."""
    user = auth_service.get_current_user(token)
    if request.report_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="report_id is required")

    pdf_content, filename = summary_service.generate_summary(
        user=user,
        report_id=request.report_id,
        include_questions=request.include_questions,
    )

    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )
