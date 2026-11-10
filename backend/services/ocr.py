import io
import os
import base64
import requests
import pytesseract
from PIL import Image

GEMINI_OCR_PROMPT = "Transcribe all text on this grocery receipt exactly as printed, one line per receipt line. Return only the text."


def _run_cloud_vision(file_bytes: bytes) -> str:
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
    annotations = resp.json()["responses"][0].get("textAnnotations", [])
    return annotations[0]["description"] if annotations else ""


def _run_tesseract(file_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(file_bytes))
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return pytesseract.image_to_string(img)


def _run_gemini_vision(file_bytes: bytes, mime_type: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [GEMINI_OCR_PROMPT, {"mime_type": mime_type, "data": file_bytes}]
    )
    return response.text


def run_ocr(file_bytes: bytes, mime_type: str) -> tuple[str, str, None]:
    """Returns (ocr_text, engine_used, confidence). Tries Cloud Vision, then Tesseract, then Gemini vision."""
    is_pdf = mime_type == "application/pdf"

    if not is_pdf and os.environ.get("GOOGLE_CLOUD_VISION_API_KEY"):
        try:
            text = _run_cloud_vision(file_bytes)
            if text.strip():
                return text, "google_cloud_vision", None
        except Exception:
            pass

    if not is_pdf:
        try:
            text = _run_tesseract(file_bytes)
            if text.strip():
                return text, "tesseract", None
        except Exception:
            pass

    text = _run_gemini_vision(file_bytes, mime_type)
    return text, "gemini_vision", None
