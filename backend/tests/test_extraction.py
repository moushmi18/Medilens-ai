"""Tests for extraction module."""
import pytest

from app.extraction import extract_lab_results, determine_abnormal_status


class TestExtractLabResults:
    """Tests for extract_lab_results function."""
    
    def test_extracts_hemoglobin(self):
        """Extract hemoglobin from text."""
        text = "Hemoglobin: 14.5 g/dL"
        results = extract_lab_results(text)
        
        assert len(results) >= 1
        hgb = next(r for r in results if "hemoglobin" in r["test_name"].lower())
        assert hgb["observed_value"] == "14.5"
        assert hgb["unit"] == "g/dL"
    
    def test_extracts_wbc(self):
        """Extract white blood cell count."""
        text = "WBC: 7.2 10^9/L"
        results = extract_lab_results(text)
        
        assert len(results) >= 1
        wbc = next(r for r in results if "wbc" in r["test_name"].lower() or "white" in r["test_name"].lower())
        assert wbc["observed_value"] == "7.2"
    
    def test_extracts_glucose(self):
        """Extract glucose level."""
        text = "Glucose: 95 mg/dL"
        results = extract_lab_results(text)
        
        assert len(results) >= 1
        glucose = next(r for r in results if "glucose" in r["test_name"].lower())
        assert glucose["observed_value"] == "95"
        assert glucose["unit"] == "mg/dL"
    
    def test_handles_table_format(self):
        """Extract from table-like format."""
        text = """
        Test Name           Value    Unit      Reference
        Hemoglobin          13.5     g/dL      12.0-16.0
        Creatinine          1.1      mg/dL     0.7-1.3
        """
        results = extract_lab_results(text)
        
        assert len(results) >= 2
    
    def test_flags_low_confidence_for_missing_unit(self):
        """Flag results with missing units."""
        text = "Hemoglobin 14.5"
        results = extract_lab_results(text)
        
        if results:
            assert results[0]["confidence_score"] < 1.0
    
    def test_flags_for_verification_when_low_confidence(self):
        """Flag uncertain extractions for verification."""
        text = "Hemoglobin: 14.5"
        results = extract_lab_results(text, ocr_confidence=0.6)
        
        if results:
            assert results[0]["needs_verification"] is True
    
    def test_no_duplicates(self):
        """Avoid duplicate results."""
        text = "Hemoglobin: 14.5 g/dL\nHemoglobin: 14.5 g/dL"
        results = extract_lab_results(text)
        
        hgb_results = [r for r in results if "hemoglobin" in r["test_name"].lower()]
        assert len(hgb_results) == 1
    
    def test_empty_text(self):
        """Handle empty text gracefully."""
        results = extract_lab_results("")
        assert results == []
    
    def test_no_lab_values(self):
        """Handle text with no lab values."""
        text = "Patient arrived for routine checkup. No abnormalities noted."
        results = extract_lab_results(text)
        assert results == []


class TestDetermineAbnormalStatus:
    """Tests for determine_abnormal_status function."""
    
    def test_normal_value(self):
        """Value within range is not abnormal."""
        result = determine_abnormal_status("14.5", "12.0", "16.0")
        assert result is False
    
    def test_low_value(self):
        """Value below range is abnormal."""
        result = determine_abnormal_status("10.0", "12.0", "16.0")
        assert result is True
    
    def test_high_value(self):
        """Value above range is abnormal."""
        result = determine_abnormal_status("18.0", "12.0", "16.0")
        assert result is True
    
    def test_only_low_range(self):
        """Only lower bound specified."""
        result = determine_abnormal_status("10.0", "12.0", None)
        assert result is True
    
    def test_only_high_range(self):
        """Only upper bound specified."""
        result = determine_abnormal_status("20.0", None, "16.0")
        assert result is True
    
    def test_no_range(self):
        """No range returns None."""
        result = determine_abnormal_status("14.5", None, None)
        assert result is None
    
    def test_invalid_value(self):
        """Invalid value returns None."""
        result = determine_abnormal_status("invalid", "12.0", "16.0")
        assert result is None
    
    def test_edge_at_low_boundary(self):
        """Value at exact low boundary is normal."""
        result = determine_abnormal_status("12.0", "12.0", "16.0")
        assert result is False
    
    def test_edge_at_high_boundary(self):
        """Value at exact high boundary is normal."""
        result = determine_abnormal_status("16.0", "12.0", "16.0")
        assert result is False
