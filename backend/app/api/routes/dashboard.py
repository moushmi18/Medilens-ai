"""Dashboard API routes."""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.database.models import Conversation, MedicalReport
from app.services.auth_service import AuthService

router = APIRouter()


class DashboardReportItem(BaseModel):
    id: str
    original_filename: str
    status: str
    uploaded_at: str | None = None
    created_at: str | None = None


class DashboardConversationItem(BaseModel):
    id: str
    title: str | None = None
    updated_at: str


class DashboardStatsResponse(BaseModel):
    total_reports: int
    processed_reports: int
    processing_reports: int
    failed_reports: int
    total_conversations: int
    recent_reports: list[DashboardReportItem]
    recent_conversations: list[DashboardConversationItem]


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    return parts[1]


@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> DashboardStatsResponse:
    """Return per-user dashboard statistics."""
    user = auth_service.get_current_user(token)

    total = db.execute(
        select(func.count()).select_from(MedicalReport).where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
        )
    ).scalar() or 0

    processed = db.execute(
        select(func.count()).select_from(MedicalReport).where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
            MedicalReport.status == "completed",
        )
    ).scalar() or 0

    processing = db.execute(
        select(func.count()).select_from(MedicalReport).where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
            MedicalReport.status == "processing",
        )
    ).scalar() or 0

    failed = db.execute(
        select(func.count()).select_from(MedicalReport).where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
            MedicalReport.status == "failed",
        )
    ).scalar() or 0

    conversations_total = db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.user_id == user.id,
        )
    ).scalar() or 0

    recent_reports = db.execute(
        select(MedicalReport)
        .where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
        )
        .order_by(MedicalReport.created_at.desc())
        .limit(5)
    ).scalars().all()

    recent_conversations = db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(5)
    ).scalars().all()

    return DashboardStatsResponse(
        total_reports=total,
        processed_reports=processed,
        processing_reports=processing,
        failed_reports=failed,
        total_conversations=conversations_total,
        recent_reports=[
            DashboardReportItem(
                id=str(r.id),
                original_filename=r.original_filename,
                status=r.status,
                uploaded_at=r.created_at.isoformat() if r.created_at else None,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in recent_reports
        ],
        recent_conversations=[
            DashboardConversationItem(
                id=str(c.id),
                title=c.title,
                updated_at=c.updated_at.isoformat() if c.updated_at else "",
            )
            for c in recent_conversations
        ],
    )
