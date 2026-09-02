from pathlib import Path
from typing import List, Union
from src.models.document_models import DocumentModel
from src.document_processing import pdf_parser, docx_parser, excel_parser, pptx_parser, image_parser
from src.utils.logger import get_logger

logger = get_logger("document_loader")


def detect_document_type(path: Union[str, Path]) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".pdf",):
        return "pdf"
    if suffix in (".docx", ".doc"):
        return "docx"
    if suffix in (".xlsx", ".xlsm", ".xls", ".csv"):
        return "excel"
    if suffix in (".pptx", ".ppt"):
        return "pptx"
    if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
        return "image"
    if suffix in (".txt",):
        return "text"
    return "unknown"


def load_documents(paths: List[Union[str, Path]], text_reader=None) -> List[DocumentModel]:
    """Load multiple documents and return normalized DocumentModel list.

    Each document parser returns a DocumentModel. Unsupported files are logged.
    """
    docs: List[DocumentModel] = []
    for p in paths:
        try:
            dtype = detect_document_type(p)
            logger.info("Processing %s as %s", p, dtype)
            if dtype == "pdf":
                doc = pdf_parser.parse_pdf(Path(p))
            elif dtype == "docx":
                doc = docx_parser.parse_docx(Path(p))
            elif dtype == "excel":
                doc = excel_parser.parse_excel(Path(p))
            elif dtype == "pptx":
                doc = pptx_parser.parse_pptx(Path(p))
            elif dtype == "image":
                doc = image_parser.parse_image(Path(p))
            elif dtype == "text":
                # simple text file
                reader = text_reader or (lambda path: Path(path).read_text(encoding="utf-8", errors="ignore"))
                text = reader(p)
                doc = DocumentModel(filename=str(p), document_type="text", paragraphs=[{
                    "text": text,
                    "location": {"filename": str(p)}
                }])
            else:
                logger.warning("Unsupported file type for %s", p)
                continue
            docs.append(doc)
        except Exception as e:
            logger.exception("Failed to process %s: %s", p, e)
    return docs
