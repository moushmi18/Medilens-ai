"""Extraction module - structured data extraction from medical documents."""
from .lab_extractor import extract_lab_results, determine_abnormal_status

__all__ = ["extract_lab_results", "determine_abnormal_status"]
