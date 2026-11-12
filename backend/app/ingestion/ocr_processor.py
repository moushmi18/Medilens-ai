"""OCR processing for scanned documents.

Primary: PaddleOCR (as per spec)
Fallback: Tesseract OCR (if PaddleOCR fails)
"""
import io
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)

_paddleocr_instance = None
_paddleocr_available = None
_tesseract_available = None


def _get_paddleocr():
    """Get or create PaddleOCR instance."""
    global _paddleocr_instance, _paddleocr_available
    
    if _paddleocr_available is False:
        return None
    
    if _paddleocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _paddleocr_instance = PaddleOCR(lang='en')
            _paddleocr_available = True
            logger.info("paddleocr_initialized")
        except Exception as e:
            _paddleocr_available = False
            logger.warning("paddleocr_init_failed", error=str(e))
            return None
    
    return _paddleocr_instance


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
    
    Uses PaddleOCR as primary engine (per spec).
    Falls back to Tesseract if PaddleOCR fails.
    
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
    
    ocr = _get_paddleocr()
    if ocr is not None:
        try:
            return _ocr_with_paddleocr(ocr, image)
        except Exception as e:
            logger.warning("paddleocr_failed_falling_back", error=str(e))
    
    if _check_tesseract():
        return _ocr_with_tesseract(image)
    
    logger.warning("ocr_not_available", message="No OCR engine available")
    return {
        "text": "",
        "lines": [],
        "confidence": 0.0,
        "ocr_engine": "none",
        "warning": "OCR not available. Install PaddleOCR or tesseract-ocr.",
    }


def _ocr_with_paddleocr(ocr, image: Image.Image) -> dict[str, Any]:
    """Perform OCR using PaddleOCR."""
    import numpy as np
    
    img_array = np.array(image.convert("RGB"))
    
    result = ocr.predict(img_array)
    
    lines = []
    texts = []
    confidences = []
    
    if result and len(result) > 0:
        for item in result:
            if hasattr(item, 'rec_texts') and hasattr(item, 'rec_scores'):
                for i, (text, score) in enumerate(zip(item.rec_texts, item.rec_scores)):
                    if text.strip():
                        texts.append(text.strip())
                        confidences.append(float(score))
                        
                        bbox = None
                        if hasattr(item, 'dt_polys') and i < len(item.dt_polys):
                            poly = item.dt_polys[i]
                            if len(poly) >= 4:
                                xs = [p[0] for p in poly]
                                ys = [p[1] for p in poly]
                                bbox = {
                                    "left": int(min(xs)),
                                    "top": int(min(ys)),
                                    "width": int(max(xs) - min(xs)),
                                    "height": int(max(ys) - min(ys)),
                                }
                        
                        lines.append({
                            "text": text.strip(),
                            "confidence": float(score),
                            "bounding_box": bbox,
                        })
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    logger.debug(
        "paddleocr_completed",
        line_count=len(texts),
        avg_confidence=avg_confidence,
    )
    
    return {
        "text": "\n".join(texts),
        "lines": lines,
        "confidence": avg_confidence,
        "ocr_engine": "paddleocr",
    }


def _ocr_with_tesseract(image: Image.Image) -> dict[str, Any]:
    """Perform OCR using Tesseract (fallback)."""
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
            "ocr_engine": page_result.get("ocr_engine", "unknown"),
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
