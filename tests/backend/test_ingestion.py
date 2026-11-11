"""Tests for document ingestion (parsing and OCR)."""
import io
import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.ingestion import (
    extract_text_from_pdf,
    compute_file_hash,
    ocr_image,
)


def create_test_image_with_text(text: str) -> bytes:
    """Create a test image with text for OCR testing."""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), text, fill="black")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()


def test_compute_file_hash():
    """Test file hash computation."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        f.flush()
        
        hash1 = compute_file_hash(f.name)
        hash2 = compute_file_hash(f.name)
        
        assert hash1 == hash2
        assert len(hash1) == 64
        
        Path(f.name).unlink()


def test_compute_file_hash_different_content():
    """Test that different content produces different hashes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f1:
        f1.write(b"content 1")
        f1.flush()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f2:
            f2.write(b"content 2")
            f2.flush()
            
            hash1 = compute_file_hash(f1.name)
            hash2 = compute_file_hash(f2.name)
            
            assert hash1 != hash2
            
            Path(f1.name).unlink()
            Path(f2.name).unlink()


@pytest.mark.slow
def test_ocr_simple_text():
    """Test OCR on a simple image with text."""
    test_text = "HEMOGLOBIN 14.2"
    image_bytes = create_test_image_with_text(test_text)
    
    result = ocr_image(image_bytes)
    
    assert "text" in result
    assert "lines" in result
    assert "confidence" in result
    assert result["confidence"] >= 0


@pytest.mark.slow
def test_ocr_result_structure():
    """Test OCR result has correct structure."""
    image_bytes = create_test_image_with_text("Test 123")
    
    result = ocr_image(image_bytes)
    
    assert isinstance(result["text"], str)
    assert isinstance(result["lines"], list)
    assert isinstance(result["confidence"], float)


def test_pdf_extraction_file_not_found():
    """Test PDF extraction with non-existent file."""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("/nonexistent/path/file.pdf")
