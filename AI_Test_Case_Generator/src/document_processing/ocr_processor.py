from pathlib import Path
from PIL import Image
import pytesseract
from src.utils.logger import get_logger

logger = get_logger("ocr_processor")


def ocr_image(path: Path, lang: str = "eng") -> str:
    """Run OCR on an image and return extracted text."""
    try:
        img = Image.open(str(path))
        text = pytesseract.image_to_string(img, lang=lang)
        return text or ""
    except Exception:
        logger.exception("OCR failed for %s", path)
        return ""
