"""Extraction service for processing medical reports."""
from pathlib import Path
from uuid import UUID

from qdrant_client import QdrantClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.models import MedicalReport, ExtractedResult, User
from app.embeddings.qdrant_client import USER_REPORTS_COLLECTION
from app.extraction import extract_lab_results, determine_abnormal_status
from app.ingestion import extract_text_from_pdf, ocr_image, ocr_pdf_pages, get_pdf_page_images
from app.ingestion.docx_parser import extract_text_from_docx

logger = get_logger(__name__)


class ExtractionService:
    """Service for extracting structured data from reports."""
    
    def __init__(self, db: Session, qdrant: QdrantClient | None = None):
        self.db = db
        self.qdrant = qdrant
    
    def process_report(self, report_id: UUID) -> list[ExtractedResult]:
        """Process a report and extract structured data."""
        report = self.db.execute(
            select(MedicalReport).where(MedicalReport.id == report_id)
        ).scalar_one_or_none()
        
        if not report:
            raise NotFoundError("Report", str(report_id))
        
        self._update_status(report, "processing")
        
        try:
            text, ocr_confidence = self._extract_text(report)
            
            raw_results = extract_lab_results(
                text=text,
                page_number=1,
                ocr_confidence=ocr_confidence,
            )
            
            results = []
            for raw in raw_results:
                is_abnormal = determine_abnormal_status(
                    raw["observed_value"],
                    raw["reference_range_low"],
                    raw["reference_range_high"],
                )
                
                result = ExtractedResult(
                    report_id=report_id,
                    test_name=raw["test_name"],
                    observed_value=raw["observed_value"],
                    unit=raw["unit"],
                    reference_range_low=raw["reference_range_low"],
                    reference_range_high=raw["reference_range_high"],
                    reference_range_text=raw["reference_range_text"],
                    is_abnormal=is_abnormal,
                    page_number=raw["page_number"],
                    confidence_score=raw["confidence_score"],
                    needs_verification=raw["needs_verification"],
                )
                self.db.add(result)
                results.append(result)
            
            self._index_report_vectors(report, text)
            
            self._update_status(report, "completed")
            self.db.commit()
            
            logger.info(
                "report_processed",
                report_id=str(report_id),
                results_count=len(results),
            )
            
            return results
            
        except Exception as e:
            self._update_status(report, "failed", str(e))
            self.db.commit()
            logger.error("report_processing_failed", report_id=str(report_id), error=str(e))
            raise
    
    def _index_report_vectors(self, report: MedicalReport, text: str) -> None:
        """Index report text into Qdrant via LlamaIndex chunking when available."""
        if not self.qdrant or not text.strip():
            return
        
        try:
            from app.knowledge.llama_integration import LlamaIndexDocumentProcessor
            
            processor = LlamaIndexDocumentProcessor(chunk_size=512, chunk_overlap=64)
            processor.ingest_to_qdrant(
                client=self.qdrant,
                collection_name=USER_REPORTS_COLLECTION,
                text=text,
                source_id=str(report.id),
                metadata={
                    "user_id": str(report.user_id),
                    "report_id": str(report.id),
                    "report_filename": report.original_filename,
                    "source_type": "user_report",
                },
            )
        except Exception as e:
            logger.warning(
                "report_vector_indexing_failed",
                report_id=str(report.id),
                error=str(e),
            )
    
    def get_results(self, user: User, report_id: UUID) -> list[ExtractedResult]:
        """Get extracted results for a report."""
        report = self.db.execute(
            select(MedicalReport).where(
                MedicalReport.id == report_id,
                MedicalReport.user_id == user.id,
            )
        ).scalar_one_or_none()
        
        if not report:
            raise NotFoundError("Report", str(report_id))
        
        results = self.db.execute(
            select(ExtractedResult).where(ExtractedResult.report_id == report_id)
        ).scalars().all()
        
        return list(results)
    
    def verify_result(
        self,
        user: User,
        result_id: UUID,
        **updates,
    ) -> ExtractedResult:
        """Verify and update an extracted result."""
        result = self.db.execute(
            select(ExtractedResult)
            .join(MedicalReport)
            .where(
                ExtractedResult.id == result_id,
                MedicalReport.user_id == user.id,
            )
        ).scalar_one_or_none()
        
        if not result:
            raise NotFoundError("ExtractedResult", str(result_id))
        
        for key, value in updates.items():
            if hasattr(result, key) and value is not None:
                setattr(result, key, value)
        
        result.needs_verification = False
        
        if result.observed_value and (result.reference_range_low or result.reference_range_high):
            result.is_abnormal = determine_abnormal_status(
                result.observed_value,
                result.reference_range_low,
                result.reference_range_high,
            )
        
        self.db.commit()
        self.db.refresh(result)
        
        return result
    
    def _extract_text(self, report: MedicalReport) -> tuple[str, float | None]:
        """Extract text from a report file."""
        file_path = Path(report.storage_path)
        
        if report.file_type == "pdf":
            result = extract_text_from_pdf(file_path)
            if result["is_scanned"]:
                page_images = get_pdf_page_images(file_path)
                ocr_result = ocr_pdf_pages(page_images)
                return ocr_result["text"], ocr_result["avg_confidence"]
            return result["text"], None
        
        elif report.file_type == "image":
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            ocr_result = ocr_image(image_bytes)
            return ocr_result["text"], ocr_result["confidence"]
        
        elif report.file_type == "docx":
            result = extract_text_from_docx(file_path)
            return result["text"], None
        
        else:
            raise ValueError(f"Unsupported file type: {report.file_type}")
    
    def _update_status(
        self,
        report: MedicalReport,
        status: str,
        error: str | None = None,
    ) -> None:
        """Update report status."""
        report.status = status
        if error:
            report.processing_error = error
        self.db.flush()
