"""Report comparison service.

Compares extracted results between two or more reports.
IMPORTANT: Shows factual changes only - NEVER diagnoses or interprets.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.models import MedicalReport, ExtractedResult, User

logger = get_logger(__name__)


@dataclass
class ResultComparison:
    """Comparison of a single test result across reports."""
    test_name: str
    reports: list[dict[str, Any]]
    change: float | None
    change_direction: str | None
    unit: str | None


@dataclass
class ComparisonResult:
    """Result of comparing multiple reports."""
    report_ids: list[UUID]
    report_dates: list[datetime]
    comparisons: list[ResultComparison]
    matched_tests: int
    unmatched_tests: int


class ComparisonService:
    """Service for comparing medical reports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compare_reports(
        self,
        user: User,
        report_ids: list[UUID],
    ) -> ComparisonResult:
        """Compare extracted results across multiple reports.
        
        Args:
            user: Current user
            report_ids: List of report IDs to compare (must be 2+)
            
        Returns:
            ComparisonResult with test-by-test comparisons
        """
        if len(report_ids) < 2:
            raise ValueError("At least 2 reports required for comparison")
        
        reports = []
        for report_id in report_ids:
            report = self.db.execute(
                select(MedicalReport).where(
                    MedicalReport.id == report_id,
                    MedicalReport.user_id == user.id,
                )
            ).scalar_one_or_none()
            
            if not report:
                raise NotFoundError("Report", str(report_id))
            reports.append(report)
        
        reports.sort(key=lambda r: r.uploaded_at)
        report_ids = [r.id for r in reports]
        report_dates = [r.uploaded_at for r in reports]
        
        all_results: dict[UUID, list[ExtractedResult]] = {}
        for report in reports:
            results = self.db.execute(
                select(ExtractedResult).where(
                    ExtractedResult.report_id == report.id
                )
            ).scalars().all()
            all_results[report.id] = list(results)
        
        test_groups = self._group_by_test_name(all_results)
        
        comparisons = []
        matched = 0
        unmatched = 0
        
        for test_name, results_by_report in test_groups.items():
            report_data = []
            values = []
            
            for report_id in report_ids:
                result = results_by_report.get(report_id)
                if result:
                    report_data.append({
                        "report_id": str(report_id),
                        "value": result.observed_value,
                        "unit": result.unit,
                        "is_abnormal": result.is_abnormal,
                        "reference_range": (
                            f"{result.reference_range_low}-{result.reference_range_high}"
                            if result.reference_range_low and result.reference_range_high
                            else None
                        ),
                    })
                    try:
                        values.append(float(result.observed_value))
                    except (ValueError, TypeError):
                        values.append(None)
                else:
                    report_data.append({
                        "report_id": str(report_id),
                        "value": None,
                        "unit": None,
                        "is_abnormal": None,
                        "reference_range": None,
                    })
                    values.append(None)
            
            if len([v for v in values if v is not None]) >= 2:
                matched += 1
                
                numeric_values = [v for v in values if v is not None]
                if len(numeric_values) >= 2:
                    change = numeric_values[-1] - numeric_values[0]
                    direction = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                else:
                    change = None
                    direction = None
            else:
                unmatched += 1
                change = None
                direction = None
            
            first_result = next(
                (r for r in results_by_report.values() if r),
                None
            )
            
            comparisons.append(ResultComparison(
                test_name=test_name,
                reports=report_data,
                change=change,
                change_direction=direction,
                unit=first_result.unit if first_result else None,
            ))
        
        logger.info(
            "reports_compared",
            user_id=str(user.id),
            report_count=len(report_ids),
            matched_tests=matched,
        )
        
        return ComparisonResult(
            report_ids=report_ids,
            report_dates=report_dates,
            comparisons=comparisons,
            matched_tests=matched,
            unmatched_tests=unmatched,
        )
    
    def _group_by_test_name(
        self,
        all_results: dict[UUID, list[ExtractedResult]],
    ) -> dict[str, dict[UUID, ExtractedResult]]:
        """Group results by normalized test name."""
        groups: dict[str, dict[UUID, ExtractedResult]] = {}
        
        for report_id, results in all_results.items():
            for result in results:
                name = self._normalize_test_name(result.test_name)
                if name not in groups:
                    groups[name] = {}
                groups[name][report_id] = result
        
        return groups
    
    def _normalize_test_name(self, name: str) -> str:
        """Normalize test name for matching."""
        return name.lower().strip()
