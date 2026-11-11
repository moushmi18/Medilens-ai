"""Health check endpoints."""
from datetime import datetime, timezone

import redis
from fastapi import APIRouter
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import SessionLocal

router = APIRouter()
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str
    checks: dict[str, bool]
    timestamp: str


def check_postgres() -> bool:
    """Check PostgreSQL connectivity."""
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning("postgres_check_failed", error=str(e))
        return False


def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_timeout=2,
        )
        client.ping()
        client.close()
        return True
    except Exception as e:
        logger.warning("redis_check_failed", error=str(e))
        return False


def check_qdrant() -> bool:
    """Check Qdrant connectivity."""
    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            timeout=2,
        )
        client.get_collections()
        client.close()
        return True
    except (UnexpectedResponse, Exception) as e:
        logger.warning("qdrant_check_failed", error=str(e))
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe - checks if the application is running."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    """Readiness probe - checks if all dependencies are available."""
    checks = {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "qdrant": check_qdrant(),
    }

    all_ready = all(checks.values())

    return ReadyResponse(
        status="ready" if all_ready else "not_ready",
        checks=checks,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
