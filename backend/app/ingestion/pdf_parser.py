"""PDF parsing using PyMuPDF."""
import hashlib
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: str | Path) -> dict[str, Any]:
    """Extract text from a digital PDF using PyMuPDF.
    
    Returns:
        dict with keys:
        - text: full extracted text
        - pages: list of page texts
        - page_count: number of pages
        - is_scanned: whether the PDF appears to be scanned (low text content)
        - metadata: PDF metadata
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    doc = fitz.open(file_path)
    
    pages = []
    full_text = []
    total_chars = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages.append({
            "page_number": page_num + 1,
            "text": text,
            "char_count": len(text),
        })
        full_text.append(text)
        total_chars += len(text)
    
    avg_chars_per_page = total_chars / len(doc) if len(doc) > 0 else 0
    is_scanned = avg_chars_per_page < 100
    
    metadata = doc.metadata or {}
    
    doc.close()
    
    logger.info(
        "pdf_extracted",
        file=str(file_path),
        page_count=len(pages),
        total_chars=total_chars,
        is_scanned=is_scanned,
    )
    
    return {
        "text": "\n\n".join(full_text),
        "pages": pages,
        "page_count": len(pages),
        "is_scanned": is_scanned,
        "metadata": metadata,
    }


def get_pdf_page_images(file_path: str | Path) -> list[bytes]:
    """Convert PDF pages to images for OCR processing.
    
    Returns list of PNG image bytes for each page.
    """
    file_path = Path(file_path)
    doc = fitz.open(file_path)
    
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        images.append(pix.tobytes("png"))
    
    doc.close()
    return images


def compute_file_hash(file_path: str | Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
