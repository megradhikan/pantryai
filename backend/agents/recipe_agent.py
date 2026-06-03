import json
import re
import os
import google.generativeai as genai
from services.embeddings import embed_text
from services.supabase_client import get_admin_client

SYSTEM_PROMPT = """You are a recipe recommender for a pantry management app.
Given a user's inventory and candidate recipes, return the 5 best suggestions.
Return ONLY valid JSON, no markdown, no preamble.

Output schema:
{
  "suggestions": [
    {
      "recipe_id": string,
      "title": string,
      "inventory_items_used": [string],
      "missing_ingredients": [{ "name": string, "quantity": float | null, "unit": string | null }],
      "match_score": float
    }
  ]
}

Rules:
- match_score: fraction of required=true ingredients covered by inventory. Range 0.0–1.0.
- inventory_items_used: list of inventory item names actually used in this recipe.
- Prioritize recipes where expiring_soon items appear in ingredients.
- missing_ingredients: only required=true ingredients not found in inventory.
- Do fuzzy matching: "heavy cream" matches "cream", "chicken breast" matches "chicken".
- Return exactly 5 suggestions, ranked by match_score descending.
"""


GENERATE_PROMPT = """You are a creative chef. Given a user's pantry inventory, create an original recipe that maximizes use of their available ingredients.
Return ONLY valid JSON.

Output schema:
{
  "title": string,
  "ingredients": [{ "name": string, "quantity": float | null, "unit": string | null, "from_pantry": bool }],
  "instructions": string,
  "cuisine": string,
  "prep_time_mins": int,
  "pantry_items_used": [string],
  "extra_items_needed": [{ "name": string, "quantity": float | null, "unit": string | null }]
}

Rules:
- Prioritize ingredients that are expiring soon.
- Use as many pantry items as possible.
- from_pantry: true if the ingredient comes from the user's inventory, false if they need to buy it.
- extra_items_needed: only items not in the pantry. Keep this list minimal — a great recipe uses mostly what's available.
- Be creative but practical — no obscure techniques or equipment.
- instructions: clear numbered steps.
"""


def _get_model(system_instruction=SYSTEM_PROMPT):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=system_instruction,
        generation_config={"response_mime_type": "application/json"},
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def suggest_recipes(inventory: list[dict]) -> list[dict]:
    active_items = [i for i in inventory if i["status"] not in ("finished", "expired")]
    if not active_items:
        return []

    query_text = " ".join(i["name"] for i in active_items)
    query_embedding = embed_text(query_text)

    supabase = get_admin_client()
    candidates = supabase.rpc(
        "match_recipes",
        {"query_embedding": query_embedding, "match_count": 20},
    ).execute().data

    inventory_json = json.dumps(
        [{"name": i["name"], "category": i["category"], "status": i["status"]} for i in active_items]
    )
    candidates_json = json.dumps(
        [
            {"recipe_id": str(c["id"]), "title": c["title"], "ingredients": c["ingredients"]}
            for c in candidates
        ]
    )

    model = _get_model()
    response = model.generate_content(
        f"Inventory:\n{inventory_json}\n\nCandidates:\n{candidates_json}"
    )
    raw = response.text.strip()
    parsed = _extract_json(raw)
    return parsed.get("suggestions", [])


def generate_recipe(inventory: list[dict]) -> dict | None:
    active_items = [i for i in inventory if i["status"] not in ("finished", "expired")]
    if not active_items:
        return None

    inventory_json = json.dumps(
        [{"name": i["name"], "category": i["category"], "status": i["status"]} for i in active_items]
    )

    model = _get_model(system_instruction=GENERATE_PROMPT)
    response = model.generate_content(f"My pantry:\n{inventory_json}")
    raw = response.text.strip()
    return _extract_json(raw)
