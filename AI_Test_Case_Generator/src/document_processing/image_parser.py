from pathlib import Path
from typing import List
from PIL import Image
from src.models.document_models import DocumentModel, ParagraphModel, ImageModel, SourceLocation
from src.document_processing.ocr_processor import ocr_image
from src.utils.logger import get_logger

logger = get_logger("image_parser")


def parse_image(path: Path) -> DocumentModel:
    """Parse an image file: run OCR and return extracted text and image metadata."""
    try:
        img = Image.open(str(path))
        # basic metadata
        metadata = {"size": img.size, "mode": img.mode}
        text = ocr_image(path)
        paragraphs: List[ParagraphModel] = []
        if text and text.strip():
            loc = SourceLocation(filename=str(path))
            paragraphs.append(ParagraphModel(text=text.strip(), location=loc))
        images = [ImageModel(filename=str(path.name), description="uploaded image", location=SourceLocation(filename=str(path)))]
        document = DocumentModel(
            filename=str(path.name),
            document_type="image",
            paragraphs=paragraphs,
            images=images,
            metadata=metadata,
            source_locations=[{"filename": str(path)}],
        )
        return document
    except Exception:
        logger.exception("Failed to parse image %s", path)
        return DocumentModel(filename=str(path.name), document_type="image", paragraphs=[], images=[], metadata={}, source_locations=[{"filename": str(path)}])
