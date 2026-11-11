"""API dependency injection utilities."""
from collections.abc import Generator
from typing import Any

from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import SessionLocal


def get_db() -> Generator[Session, Any, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_qdrant() -> QdrantClient:
    """Dependency to get Qdrant client."""
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )
