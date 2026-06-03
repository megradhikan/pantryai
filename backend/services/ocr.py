import io
import pytesseract
from PIL import Image


def run_ocr(file_bytes: bytes, mime_type: str) -> tuple[str, str, None]:
    """
    Returns (ocr_text, engine_used, confidence_score).
    Uses Tesseract only. confidence_score is always None (not provided by pytesseract).
    """
    img = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(img)
    return text, "tesseract", None
