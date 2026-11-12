"""Automatic retention purge for user reports past retention_days."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient

from app.core.logging import get_logger
from app.database.models import ExtractedResult, MedicalReport, User
from app.embeddings.qdrant_client import delete_user_report_vectors

logger = get_logger(__name__)


class RetentionService:
    """Purge reports older than each user's retention preference."""

    def __init__(self, db: Session, qdrant: QdrantClient | None = None):
        self.db = db
        self.qdrant = qdrant

    def find_expired_reports(
        self,
        now: datetime | None = None,
    ) -> list[MedicalReport]:
        """Return non-deleted reports past each owner's retention window.

        Users with retention_days == 0 are skipped (manual deletion only).
        """
        now = now or datetime.now(timezone.utc)
        users = self.db.execute(
            select(User).where(User.retention_days > 0)
        ).scalars().all()

        expired: list[MedicalReport] = []
        for user in users:
            cutoff = now - timedelta(days=user.retention_days)
            reports = self.db.execute(
                select(MedicalReport).where(
                    MedicalReport.user_id == user.id,
                    MedicalReport.deleted_at.is_(None),
                    MedicalReport.created_at < cutoff,
                )
            ).scalars().all()
            expired.extend(list(reports))
        return expired

    def purge_report(self, report: MedicalReport) -> dict[str, Any]:
        """Hard-delete one report: vectors, extracted results, file, DB row."""
        result = {
            "report_id": str(report.id),
            "user_id": str(report.user_id),
            "file_deleted": False,
            "vectors_deleted": False,
            "results_deleted": 0,
        }

        if self.qdrant is not None:
            try:
                delete_user_report_vectors(self.qdrant, report.user_id, report.id)
                result["vectors_deleted"] = True
            except Exception as e:
                logger.warning(
                    "retention_vector_delete_failed",
                    report_id=str(report.id),
                    error=str(e),
                )

        results = self.db.execute(
            select(ExtractedResult).where(ExtractedResult.report_id == report.id)
        ).scalars().all()
        for row in results:
            self.db.delete(row)
        result["results_deleted"] = len(results)

        storage_path = Path(report.storage_path) if report.storage_path else None
        if storage_path and storage_path.exists():
            try:
                os.remove(storage_path)
                result["file_deleted"] = True
            except OSError as e:
                logger.warning(
                    "retention_file_delete_failed",
                    path=str(storage_path),
                    error=str(e),
                )

        self.db.delete(report)
        self.db.flush()
        return result

    def purge_expired(self, now: datetime | None = None) -> dict[str, Any]:
        """Purge all expired reports across users."""
        expired = self.find_expired_reports(now=now)
        purged = []
        for report in expired:
            purged.append(self.purge_report(report))
        self.db.commit()

        summary = {
            "purged_count": len(purged),
            "reports": purged,
        }
        logger.info("retention_purge_complete", purged_count=len(purged))
        return summary
