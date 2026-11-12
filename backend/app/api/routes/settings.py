"""User settings API routes."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.schemas.settings import (
    SettingsResponse,
    UserPreferences,
    UserPreferencesUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/settings")

DEFAULT_PREFERENCES = {
    "email_notifications": True,
    "processing_alerts": True,
    "dark_mode": False,
    "show_confidence": True,
    "auto_process": False,
}


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    return parts[1]


def _merged_preferences(raw: dict | None) -> UserPreferences:
    data = {**DEFAULT_PREFERENCES, **(raw or {})}
    return UserPreferences.model_validate(data)


@router.get("", response_model=SettingsResponse)
def get_settings(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> SettingsResponse:
    """Load the current user's preferences."""
    user = auth_service.get_current_user(token)
    return SettingsResponse(
        preferences=_merged_preferences(user.preferences if isinstance(user.preferences, dict) else None),
        retention_days=user.retention_days,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(
    request: UserPreferencesUpdate,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Persist notification/display preference toggles."""
    user = auth_service.get_current_user(token)
    current = {**DEFAULT_PREFERENCES, **(user.preferences or {})}
    updates = request.model_dump(exclude_unset=True)
    current.update({k: v for k, v in updates.items() if v is not None})
    user.preferences = current
    db.commit()
    db.refresh(user)
    return SettingsResponse(
        preferences=_merged_preferences(user.preferences),
        retention_days=user.retention_days,
    )
