"""OCR processing for scanned documents.

Note: PaddleOCR 3.x has compatibility issues. This module provides a fallback
using Tesseract OCR when available, or returns empty results when OCR is not available.
"""
import io
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)

_ocr_available = None
_tesseract_available = None


def _check_tesseract() -> bool:
    """Check if Tesseract OCR is available."""
    global _tesseract_available
    if _tesseract_available is None:
        _tesseract_available = shutil.which("tesseract") is not None
        if _tesseract_available:
            try:
                import pytesseract
                _tesseract_available = True
            except ImportError:
                _tesseract_available = False
    return _tesseract_available


def ocr_image(image_data: bytes | str | Path) -> dict[str, Any]:
    """Perform OCR on an image.
    
    Uses Tesseract OCR if available. Falls back to empty result if not.
    
    Args:
        image_data: Image as bytes, file path string, or Path object
        
    Returns:
        dict with keys:
        - text: extracted text
        - lines: list of detected text lines with confidence
        - confidence: average confidence score
        - ocr_engine: which OCR engine was used
    """
    if isinstance(image_data, bytes):
        image = Image.open(io.BytesIO(image_data))
    elif isinstance(image_data, (str, Path)):
        image = Image.open(image_data)
    else:
        raise ValueError(f"Unsupported image_data type: {type(image_data)}")
    
    if _check_tesseract():
        return _ocr_with_tesseract(image)
    
    logger.warning("ocr_not_available", message="No OCR engine available")
    return {
        "text": "",
        "lines": [],
        "confidence": 0.0,
        "ocr_engine": "none",
        "warning": "OCR not available. Install tesseract-ocr and pytesseract.",
    }


def _ocr_with_tesseract(image: Image.Image) -> dict[str, Any]:
    """Perform OCR using Tesseract."""
    import pytesseract
    
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    lines = []
    texts = []
    confidences = []
    
    current_line = []
    current_line_num = -1
    
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = data["conf"][i]
        line_num = data["line_num"][i]
        
        if line_num != current_line_num and current_line:
            line_text = " ".join(current_line)
            if line_text:
                texts.append(line_text)
            current_line = []
        
        current_line_num = line_num
        
        if text and conf > 0:
            current_line.append(text)
            lines.append({
                "text": text,
                "confidence": conf / 100.0,
                "bounding_box": {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                },
            })
            confidences.append(conf / 100.0)
    
    if current_line:
        line_text = " ".join(current_line)
        if line_text:
            texts.append(line_text)
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    logger.debug(
        "tesseract_ocr_completed",
        line_count=len(texts),
        avg_confidence=avg_confidence,
    )
    
    return {
        "text": "\n".join(texts),
        "lines": lines,
        "confidence": avg_confidence,
        "ocr_engine": "tesseract",
    }


def ocr_pdf_pages(page_images: list[bytes]) -> dict[str, Any]:
    """Perform OCR on multiple PDF page images.
    
    Args:
        page_images: List of PNG image bytes for each page
        
    Returns:
        dict with keys:
        - text: full extracted text
        - pages: list of page OCR results
        - avg_confidence: average confidence across all pages
    """
    pages = []
    all_texts = []
    all_confidences = []
    
    for i, image_bytes in enumerate(page_images):
        page_result = ocr_image(image_bytes)
        pages.append({
            "page_number": i + 1,
            "text": page_result["text"],
            "lines": page_result["lines"],
            "confidence": page_result["confidence"],
        })
        all_texts.append(page_result["text"])
        if page_result["confidence"] > 0:
            all_confidences.append(page_result["confidence"])
    
    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    
    logger.info(
        "pdf_ocr_completed",
        page_count=len(pages),
        avg_confidence=avg_confidence,
    )
    
    return {
        "text": "\n\n".join(all_texts),
        "pages": pages,
        "avg_confidence": avg_confidence,
    }
