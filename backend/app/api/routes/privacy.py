"""Privacy and user settings API routes."""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.services.auth_service import AuthService

router = APIRouter(prefix="/privacy")


class RetentionSettings(BaseModel):
    retention_days: int = Field(..., ge=0, le=3650)


class RetentionResponse(BaseModel):
    retention_days: int


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    return parts[1]


@router.get("/retention", response_model=RetentionResponse)
def get_retention(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> RetentionResponse:
    """Get the current user's data retention setting."""
    user = auth_service.get_current_user(token)
    return RetentionResponse(retention_days=user.retention_days)


@router.put("/retention", response_model=RetentionResponse)
def update_retention(
    request: RetentionSettings,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> RetentionResponse:
    """Update the current user's data retention setting (days; 0 = manual only)."""
    user = auth_service.get_current_user(token)
    user.retention_days = request.retention_days
    db.commit()
    db.refresh(user)
    return RetentionResponse(retention_days=user.retention_days)
