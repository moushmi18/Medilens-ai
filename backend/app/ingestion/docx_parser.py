"""DOCX document parsing using python-docx."""
from pathlib import Path
from typing import Any

from docx import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_docx(file_path: str | Path) -> dict[str, Any]:
    """Extract text from a DOCX file.
    
    Returns:
        dict with keys:
        - text: full extracted text
        - paragraphs: list of paragraph texts
        - tables: list of table data
        - metadata: document properties
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    
    doc = Document(file_path)
    
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        if table_data:
            tables.append(table_data)
    
    core_props = doc.core_properties
    metadata = {
        "author": core_props.author,
        "title": core_props.title,
        "subject": core_props.subject,
        "created": str(core_props.created) if core_props.created else None,
        "modified": str(core_props.modified) if core_props.modified else None,
    }
    
    full_text = "\n\n".join(paragraphs)
    
    for table_data in tables:
        table_text = "\n".join([" | ".join(row) for row in table_data])
        full_text += f"\n\n{table_text}"
    
    logger.info(
        "docx_extracted",
        file=str(file_path),
        paragraph_count=len(paragraphs),
        table_count=len(tables),
    )
    
    return {
        "text": full_text,
        "paragraphs": paragraphs,
        "tables": tables,
        "metadata": metadata,
    }
