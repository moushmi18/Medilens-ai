"""Authentication API routes."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import AuthenticationError
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    """Extract token from Authorization header."""
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new user account."""
    user = auth_service.register(user_data)
    return auth_service.create_tokens(user)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Login with email and password."""
    user = auth_service.authenticate(credentials.email, credentials.password)
    return auth_service.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    return auth_service.refresh_tokens(refresh_data.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Get current authenticated user."""
    user = auth_service.get_current_user(token)
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=204)
def logout() -> None:
    """Logout (client should discard tokens)."""
    pass
