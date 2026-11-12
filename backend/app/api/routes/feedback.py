"""Feedback API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.database.models import Feedback
from app.services.auth_service import AuthService

router = APIRouter(prefix="/feedback")


class FeedbackRequest(BaseModel):
    message_id: UUID | None = None
    feedback_type: str = Field(..., pattern="^(helpful|not_helpful|incorrect|missing_info)$")
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    feedback_type: str


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    return parts[1]


@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    request: FeedbackRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Submit user feedback on an assistant response."""
    user = auth_service.get_current_user(token)

    # Accept camelCase from frontend as well via aliases handled in route body
    feedback = Feedback(
        user_id=user.id,
        message_id=request.message_id,
        feedback_type=request.feedback_type,
        comment=request.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(id=str(feedback.id), feedback_type=feedback.feedback_type)
