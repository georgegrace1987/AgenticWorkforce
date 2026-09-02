from typing import List
from src.models.document_models import DocumentModel, ParagraphModel
from src.utils.logger import get_logger

logger = get_logger("document_normalizer")


def normalize_documents(docs: List[DocumentModel]) -> List[DocumentModel]:
    """Normalize a list of DocumentModel objects.

    Current normalization steps:
    - Trim paragraph text
    - Remove empty paragraphs
    - Ensure document_type is set
    - Preserve source_locations
    """
    normalized: List[DocumentModel] = []
    for doc in docs:
        try:
            paras = []
            for p in doc.paragraphs or []:
                text = p.text.strip()
                if text:
                    paras.append(ParagraphModel(text=text, location=p.location))
            doc.paragraphs = paras
            if not getattr(doc, "document_type", None):
                doc.document_type = "unknown"
            normalized.append(doc)
        except Exception:
            logger.exception("Failed to normalize document %s", getattr(doc, "filename", "unknown"))
    return normalized
