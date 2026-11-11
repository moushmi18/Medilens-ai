"""Report management service."""
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.database.models import MedicalReport, User
from app.ingestion import compute_file_hash

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


class ReportService:
    """Service for report management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_report(
        self,
        user: User,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> MedicalReport:
        """Upload a new medical report."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
            )
        
        user_dir = self.upload_dir / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = user_dir / f"temp_{uuid.uuid4().hex}{ext}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        file_hash = compute_file_hash(temp_path)
        
        existing = self.db.execute(
            select(MedicalReport).where(
                MedicalReport.user_id == user.id,
                MedicalReport.file_hash == file_hash,
                MedicalReport.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        
        if existing:
            os.remove(temp_path)
            raise ValidationError("This file has already been uploaded")
        
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        final_path = user_dir / stored_filename
        os.rename(temp_path, final_path)
        
        file_type = self._get_file_type(ext)
        
        report = MedicalReport(
            user_id=user.id,
            filename=stored_filename,
            original_filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=str(final_path),
            status="uploaded",
            ocr_required=file_type in ("image", "scanned_pdf"),
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        logger.info(
            "report_uploaded",
            report_id=str(report.id),
            user_id=str(user.id),
            file_type=file_type,
            file_size=file_size,
        )
        
        return report
    
    def get_report(self, user: User, report_id: uuid.UUID) -> MedicalReport:
        """Get a report by ID for a specific user."""
        report = self.db.execute(
            select(MedicalReport).where(
                MedicalReport.id == report_id,
                MedicalReport.user_id == user.id,
                MedicalReport.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        
        if not report:
            raise NotFoundError("Report", str(report_id))
        
        return report
    
    def list_reports(
        self,
        user: User,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[MedicalReport], int]:
        """List reports for a user with pagination."""
        offset = (page - 1) * page_size
        
        query = select(MedicalReport).where(
            MedicalReport.user_id == user.id,
            MedicalReport.deleted_at.is_(None),
        ).order_by(MedicalReport.created_at.desc())
        
        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar_one()
        
        reports = self.db.execute(
            query.offset(offset).limit(page_size)
        ).scalars().all()
        
        return list(reports), total
    
    def delete_report(self, user: User, report_id: uuid.UUID) -> None:
        """Soft delete a report."""
        report = self.get_report(user, report_id)
        
        from datetime import datetime, timezone
        report.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(
            "report_deleted",
            report_id=str(report_id),
            user_id=str(user.id),
        )
    
    def update_status(
        self,
        report_id: uuid.UUID,
        status: str,
        error: str | None = None,
        **kwargs,
    ) -> MedicalReport:
        """Update report processing status."""
        report = self.db.execute(
            select(MedicalReport).where(MedicalReport.id == report_id)
        ).scalar_one_or_none()
        
        if not report:
            raise NotFoundError("Report", str(report_id))
        
        report.status = status
        if error:
            report.processing_error = error
        
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def _get_file_type(self, ext: str) -> str:
        """Determine file type from extension."""
        if ext == ".pdf":
            return "pdf"
        elif ext in (".jpg", ".jpeg", ".png"):
            return "image"
        elif ext == ".docx":
            return "docx"
        return "unknown"
