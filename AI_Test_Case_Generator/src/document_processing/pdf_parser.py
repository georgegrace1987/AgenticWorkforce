from pathlib import Path
from typing import List
import fitz  # PyMuPDF
from src.models.document_models import DocumentModel, ParagraphModel, SourceLocation
from src.utils.logger import get_logger

logger = get_logger("pdf_parser")


def parse_pdf(path: Path) -> DocumentModel:
    """Parse a PDF file into a DocumentModel. Extracts text per page and metadata.

    Tables are not extracted in this MVP; images are noted but not saved.
    """
    doc = fitz.open(str(path))
    paragraphs: List[ParagraphModel] = []
    for i, page in enumerate(doc, start=1):
        try:
            text = page.get_text("text")
            if text and text.strip():
                loc = SourceLocation(filename=str(path), page_number=i)
                paragraphs.append(ParagraphModel(text=text.strip(), location=loc))
        except Exception:
            logger.exception("Error extracting text from page %s of %s", i, path)

    metadata = doc.metadata or {}
    document = DocumentModel(
        filename=str(path.name),
        document_type="pdf",
        paragraphs=paragraphs,
        metadata=metadata,
        source_locations=[{"filename": str(path)}],
    )
    doc.close()
    return document
