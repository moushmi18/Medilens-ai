"""Celery task definitions."""
from .celery_app import celery_app


@celery_app.task(name="ping")
def ping() -> str:
    """Trivial ping task for testing Celery connectivity."""
    return "pong"


@celery_app.task(name="purge_expired_user_data")
def purge_expired_user_data() -> dict:
    """Periodic retention purge: delete reports older than each user's preference.

    Removes extracted results, on-disk files, and Qdrant vectors for expired reports.
    Users with retention_days=0 are skipped (manual deletion only).
    """
    from app.database.session import SessionLocal
    from app.embeddings.qdrant_client import get_qdrant_client
    from app.services.retention_service import RetentionService

    db = SessionLocal()
    try:
        try:
            qdrant = get_qdrant_client()
        except Exception:
            qdrant = None
        service = RetentionService(db, qdrant=qdrant)
        return service.purge_expired()
    finally:
        db.close()
