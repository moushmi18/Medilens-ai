"""User settings / preferences schemas."""
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """Persisted UI/notification preferences."""

    email_notifications: bool = True
    processing_alerts: bool = True
    dark_mode: bool = False
    show_confidence: bool = True
    auto_process: bool = False


class UserPreferencesUpdate(BaseModel):
    """Partial update for preferences."""

    email_notifications: bool | None = None
    processing_alerts: bool | None = None
    dark_mode: bool | None = None
    show_confidence: bool | None = None
    auto_process: bool | None = None


class SettingsResponse(BaseModel):
    preferences: UserPreferences
    retention_days: int = Field(..., ge=0)
