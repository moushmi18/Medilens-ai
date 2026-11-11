"""Celery task definitions."""
from .celery_app import celery_app


@celery_app.task(name="ping")
def ping() -> str:
    """Trivial ping task for testing Celery connectivity."""
    return "pong"
