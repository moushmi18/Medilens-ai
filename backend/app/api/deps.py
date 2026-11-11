"""API dependency injection utilities."""
from collections.abc import Generator
from typing import Any

from sqlalchemy.orm import Session

from app.database.session import SessionLocal


def get_db() -> Generator[Session, Any, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
