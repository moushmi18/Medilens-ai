"""Tests for automatic retention purge."""
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from app.database import Base, engine, SessionLocal
from app.database.models import ExtractedResult, MedicalReport, User
from app.services.retention_service import RetentionService
from app.workers.celery_app import celery_app
from app.workers.tasks import purge_expired_user_data


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _make_user(db, retention_days: int, email: str | None = None) -> User:
    user = User(
        email=email or f"ret_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
        full_name="Retention Tester",
        retention_days=retention_days,
        preferences={
            "email_notifications": True,
            "processing_alerts": True,
            "dark_mode": False,
            "show_confidence": True,
            "auto_process": False,
        },
    )
    db.add(user)
    db.flush()
    return user


def _make_report(
    db,
    user: User,
    *,
    created_at: datetime,
    storage_path: Path,
) -> MedicalReport:
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(b"%PDF-1.4 retention-test")
    report = MedicalReport(
        user_id=user.id,
        filename=storage_path.name,
        original_filename="old_report.pdf",
        file_type="pdf",
        file_size=storage_path.stat().st_size,
        file_hash=uuid.uuid4().hex,
        storage_path=str(storage_path),
        status="completed",
        ocr_required=False,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(report)
    db.flush()

    result = ExtractedResult(
        report_id=report.id,
        test_name="Hemoglobin",
        observed_value="14.0",
        unit="g/dL",
        needs_verification=False,
    )
    db.add(result)
    db.commit()
    db.refresh(report)
    return report


def test_purge_deletes_expired_report_file_and_results(db, tmp_path):
    user = _make_user(db, retention_days=30)
    old = datetime.now(timezone.utc) - timedelta(days=45)
    report = _make_report(db, user, created_at=old, storage_path=tmp_path / "old.pdf")

    service = RetentionService(db, qdrant=None)
    summary = service.purge_expired(now=datetime.now(timezone.utc))

    assert summary["purged_count"] == 1
    assert not Path(report.storage_path).exists()

    remaining = db.execute(
        select(MedicalReport).where(MedicalReport.id == report.id)
    ).scalar_one_or_none()
    assert remaining is None

    results = db.execute(
        select(ExtractedResult).where(ExtractedResult.report_id == report.id)
    ).scalars().all()
    assert results == []


def test_purge_skips_reports_within_retention(db, tmp_path):
    user = _make_user(db, retention_days=90)
    recent = datetime.now(timezone.utc) - timedelta(days=10)
    report = _make_report(db, user, created_at=recent, storage_path=tmp_path / "recent.pdf")

    service = RetentionService(db, qdrant=None)
    summary = service.purge_expired()

    assert summary["purged_count"] == 0
    assert Path(report.storage_path).exists()
    assert db.execute(
        select(MedicalReport).where(MedicalReport.id == report.id)
    ).scalar_one_or_none() is not None


def test_purge_skips_retention_days_zero(db, tmp_path):
    user = _make_user(db, retention_days=0)
    ancient = datetime.now(timezone.utc) - timedelta(days=1000)
    report = _make_report(db, user, created_at=ancient, storage_path=tmp_path / "keep.pdf")

    service = RetentionService(db, qdrant=None)
    summary = service.purge_expired()

    assert summary["purged_count"] == 0
    assert Path(report.storage_path).exists()


def test_celery_beat_schedules_purge():
    schedule = celery_app.conf.beat_schedule
    assert "purge-expired-user-data-daily" in schedule
    entry = schedule["purge-expired-user-data-daily"]
    assert entry["task"] == "purge_expired_user_data"


def test_purge_task_callable(db, tmp_path, monkeypatch):
    """Task runs against DB and returns a summary dict."""
    user = _make_user(db, retention_days=7)
    old = datetime.now(timezone.utc) - timedelta(days=30)
    _make_report(db, user, created_at=old, storage_path=tmp_path / "task.pdf")
    db.close()

    # Task opens its own session; tables already created by fixture
    summary = purge_expired_user_data()
    assert isinstance(summary, dict)
    assert "purged_count" in summary
    assert summary["purged_count"] >= 1
