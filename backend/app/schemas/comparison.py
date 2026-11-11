"""Comparison Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CompareRequest(BaseModel):
    """Request to compare reports."""
    report_ids: list[UUID]


class ReportValue(BaseModel):
    """A single report's value for a test."""
    report_id: str
    value: str | None
    unit: str | None
    is_abnormal: bool | None
    reference_range: str | None


class TestComparison(BaseModel):
    """Comparison of a single test across reports."""
    test_name: str
    reports: list[ReportValue]
    change: float | None
    change_direction: str | None
    unit: str | None


class ComparisonResponse(BaseModel):
    """Response for report comparison."""
    report_ids: list[UUID]
    report_dates: list[datetime]
    comparisons: list[TestComparison]
    matched_tests: int
    unmatched_tests: int


class SummaryRequest(BaseModel):
    """Request to generate doctor summary."""
    include_questions: bool = True
