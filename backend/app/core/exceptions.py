"""Custom exception classes for the application."""
from typing import Any


class MediLensException(Exception):
    """Base exception for MediLens AI."""

    def __init__(self, message: str, code: str | None = None, details: Any | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details


class NotFoundError(MediLensException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str | None = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, code="NOT_FOUND")


class ValidationError(MediLensException):
    """Validation error."""

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class AuthenticationError(MediLensException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(MediLensException):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="AUTHORIZATION_ERROR")


class ServiceUnavailableError(MediLensException):
    """External service unavailable error."""

    def __init__(self, service: str, message: str | None = None):
        msg = f"Service '{service}' is unavailable"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(msg, code="SERVICE_UNAVAILABLE")
