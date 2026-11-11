"""Lab result extraction from medical report text.

This module extracts structured lab results from raw text using pattern matching.
IMPORTANT: Never invents values, units, or ranges - only extracts what's present.
Uncertain extractions are flagged for user verification.
"""
import re
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.database.models import ExtractedResult

logger = get_logger(__name__)

COMMON_TEST_PATTERNS = [
    r"(?P<test>hemoglobin|hgb)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>g/dL|g/L)?",
    r"(?P<test>white blood cells?|wbc)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>10\^9/L|K/uL)?",
    r"(?P<test>red blood cells?|rbc)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>10\^12/L|M/uL)?",
    r"(?P<test>platelets?|plt)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>10\^9/L|K/uL)?",
    r"(?P<test>hematocrit|hct)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>%)?",
    r"(?P<test>glucose|blood sugar)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|mmol/L)?",
    r"(?P<test>creatinine)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|umol/L)?",
    r"(?P<test>cholesterol|total cholesterol)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|mmol/L)?",
    r"(?P<test>ldl|ldl cholesterol)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|mmol/L)?",
    r"(?P<test>hdl|hdl cholesterol)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|mmol/L)?",
    r"(?P<test>triglycerides)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mg/dL|mmol/L)?",
    r"(?P<test>tsh|thyroid stimulating hormone)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mIU/L|uIU/mL)?",
    r"(?P<test>sodium|na)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mEq/L|mmol/L)?",
    r"(?P<test>potassium|k)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>mEq/L|mmol/L)?",
    r"(?P<test>mcv)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>fL)?",
    r"(?P<test>mch)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>pg)?",
    r"(?P<test>mchc)\s*[:\-]?\s*(?P<value>[\d.]+)\s*(?P<unit>g/dL)?",
]

TABLE_ROW_PATTERN = re.compile(
    r"(?P<test>[A-Za-z][A-Za-z\s\-()]+?)\s+"
    r"(?P<value>[\d.]+)\s+"
    r"(?P<unit>[A-Za-z/%^0-9]+)?\s*"
    r"(?P<range>[\d.\-\s]+(?:to|-)[\d.\s]+)?",
    re.IGNORECASE
)

REFERENCE_RANGE_PATTERN = re.compile(
    r"(?P<low>[\d.]+)\s*[-–to]+\s*(?P<high>[\d.]+)"
)


def extract_lab_results(
    text: str,
    page_number: int | None = None,
    ocr_confidence: float | None = None,
) -> list[dict[str, Any]]:
    """Extract structured lab results from text.
    
    Args:
        text: Raw text from document
        page_number: Page number in source document
        ocr_confidence: OCR confidence score if from scanned doc
        
    Returns:
        List of extracted results with structure:
        - test_name: Name of the test
        - observed_value: Extracted value (preserved as string)
        - unit: Unit of measurement if found
        - reference_range_low: Lower bound if found
        - reference_range_high: Upper bound if found
        - reference_range_text: Raw range text
        - confidence_score: Extraction confidence
        - needs_verification: Whether to flag for user review
        - page_number: Source page
    """
    results = []
    text_lower = text.lower()
    
    for pattern_str in COMMON_TEST_PATTERNS:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        for match in pattern.finditer(text):
            result = _process_match(match, page_number, ocr_confidence)
            if result and not _is_duplicate(result, results):
                results.append(result)
    
    for match in TABLE_ROW_PATTERN.finditer(text):
        result = _process_table_row(match, page_number, ocr_confidence)
        if result and not _is_duplicate(result, results):
            results.append(result)
    
    logger.info(
        "lab_results_extracted",
        count=len(results),
        page=page_number,
    )
    
    return results


def _process_match(
    match: re.Match,
    page_number: int | None,
    ocr_confidence: float | None,
) -> dict[str, Any] | None:
    """Process a regex match into a result dict."""
    try:
        test_name = match.group("test").strip().title()
        value = match.group("value")
        unit = match.groupdict().get("unit", "").strip() if match.groupdict().get("unit") else None
        
        confidence = _calculate_confidence(value, unit, ocr_confidence)
        needs_verification = confidence < 0.8
        
        return {
            "test_name": test_name,
            "observed_value": value,
            "unit": unit,
            "reference_range_low": None,
            "reference_range_high": None,
            "reference_range_text": None,
            "confidence_score": confidence,
            "needs_verification": needs_verification,
            "page_number": page_number,
        }
    except (IndexError, AttributeError):
        return None


def _process_table_row(
    match: re.Match,
    page_number: int | None,
    ocr_confidence: float | None,
) -> dict[str, Any] | None:
    """Process a table row match into a result dict."""
    try:
        test_name = match.group("test").strip()
        
        if len(test_name) < 2 or len(test_name) > 50:
            return None
        if not re.search(r'[a-zA-Z]', test_name):
            return None
        
        value = match.group("value")
        unit = match.groupdict().get("unit", "").strip() if match.groupdict().get("unit") else None
        range_text = match.groupdict().get("range", "").strip() if match.groupdict().get("range") else None
        
        range_low, range_high = None, None
        if range_text:
            range_match = REFERENCE_RANGE_PATTERN.search(range_text)
            if range_match:
                range_low = range_match.group("low")
                range_high = range_match.group("high")
        
        confidence = _calculate_confidence(value, unit, ocr_confidence)
        needs_verification = confidence < 0.8 or (range_text and not range_low)
        
        return {
            "test_name": test_name.title(),
            "observed_value": value,
            "unit": unit,
            "reference_range_low": range_low,
            "reference_range_high": range_high,
            "reference_range_text": range_text,
            "confidence_score": confidence,
            "needs_verification": needs_verification,
            "page_number": page_number,
        }
    except (IndexError, AttributeError):
        return None


def _calculate_confidence(
    value: str,
    unit: str | None,
    ocr_confidence: float | None,
) -> float:
    """Calculate confidence score for an extraction."""
    confidence = 1.0
    
    if ocr_confidence is not None:
        confidence *= ocr_confidence
    
    try:
        float(value)
    except ValueError:
        confidence *= 0.5
    
    if not unit:
        confidence *= 0.9
    
    return min(1.0, max(0.0, confidence))


def _is_duplicate(
    new_result: dict[str, Any],
    existing_results: list[dict[str, Any]],
) -> bool:
    """Check if a result is a duplicate of an existing one."""
    for existing in existing_results:
        if (existing["test_name"].lower() == new_result["test_name"].lower() and
            existing["observed_value"] == new_result["observed_value"]):
            return True
    return False


def determine_abnormal_status(
    value: str,
    range_low: str | None,
    range_high: str | None,
) -> bool | None:
    """Determine if a value is outside the reference range.
    
    Returns None if cannot determine (missing range or invalid values).
    IMPORTANT: This only flags if outside range, does NOT diagnose.
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return None
    
    if range_low is None and range_high is None:
        return None
    
    try:
        if range_low is not None and val < float(range_low):
            return True
        if range_high is not None and val > float(range_high):
            return True
        return False
    except (ValueError, TypeError):
        return None
