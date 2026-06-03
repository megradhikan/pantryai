import json
import re
import os
import google.generativeai as genai
from models.schemas import ExtractedItem, ExtractionMetadata

SYSTEM_PROMPT = """You are a grocery receipt parser.
Given raw OCR text from a grocery receipt, extract purchased items.
Return ONLY valid JSON — no markdown fences, no preamble, no explanation.

Output schema:
{
  "store_name": string | null,
  "items": [
    {
      "name": string,
      "quantity": number,
      "unit": string | null,
      "category": string
    }
  ]
}

Rules:
- name: normalized to Title Case. Expand abbreviations: CHKN BRST → Chicken Breast, LG → Large, OJ → Orange Juice
- quantity: numeric. Default 1 if not specified. For multi-packs: EGGS 12CT → quantity 12
- unit: oz | lbs | count | pack | gallon | liter | null. Use null if unclear.
- category: exactly one of: Dairy | Protein | Produce | Grains | Snacks | Beverages | Frozen | Condiments | Other
- Ignore: prices, taxes, store address, cashier name, receipt number, subtotals, totals, loyalty points
- If OCR text is empty or has no food items: return {"store_name": null, "items": []}
"""


def _get_model():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
    )


def _extract_json(text: str) -> dict:
    """Extract JSON from response, stripping markdown fences if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def extract_items(ocr_text: str) -> tuple[list[ExtractedItem], str | None, ExtractionMetadata]:
    """
    Returns (items, store_name, metadata).
    Never raises — returns empty items list on any failure.
    """
    try:
        model = _get_model()
        response = model.generate_content(ocr_text)
        raw = response.text.strip()
        parsed = _extract_json(raw)
        items = [ExtractedItem(**i) for i in parsed.get("items", [])]
        store_name = parsed.get("store_name")
        metadata = ExtractionMetadata(
            ocr_engine="",
            item_count=len(items),
            parse_success=True,
        )
        return items, store_name, metadata
    except Exception as e:
        print(f"RECEIPT AGENT ERROR: {type(e).__name__}: {e}")
        return [], None, ExtractionMetadata(ocr_engine="", item_count=0, parse_success=False)
