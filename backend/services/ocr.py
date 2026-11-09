import io
import os
import base64
import requests
import pytesseract
from PIL import Image


def _run_cloud_vision(file_bytes: bytes) -> str:
    """Call Google Cloud Vision TEXT_DETECTION via REST API."""
    api_key = os.environ["GOOGLE_CLOUD_VISION_API_KEY"]
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(file_bytes).decode("utf-8")},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
            }
        ]
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    annotations = data["responses"][0].get("textAnnotations", [])
    if not annotations:
        return ""
    return annotations[0]["description"]


def run_ocr(file_bytes: bytes, mime_type: str) -> tuple[str, str, None]:
    """
    Returns (ocr_text, engine_used, confidence_score).
    Uses Google Cloud Vision when GOOGLE_CLOUD_VISION_API_KEY is set,
    falls back to Tesseract otherwise (or on any Cloud Vision error).
    confidence_score is always None.
    """
    if os.environ.get("GOOGLE_CLOUD_VISION_API_KEY"):
        try:
            text = _run_cloud_vision(file_bytes)
            return text, "google_cloud_vision", None
        except Exception:
            pass

    img = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(img)
    return text, "tesseract", None
