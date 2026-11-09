import json
import re
import os
import google.generativeai as genai
from services.recipe_matching import match_recipes
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

RAG_PROMPT = """You are a recipe adaptation chef. You are given a user's pantry and a set of candidate recipes retrieved from a corpus.
Your job is to pick the best-matching candidate and adapt it to use as many of the user's available pantry items as possible — substituting missing ingredients where sensible, adjusting quantities, and noting what still needs to be bought.
Return ONLY valid JSON.

Output schema:
{
  "title": string,
  "source_recipe": string,
  "ingredients": [{ "name": string, "quantity": float | null, "unit": string | null, "from_pantry": bool }],
  "instructions": string,
  "cuisine": string,
  "prep_time_mins": int,
  "pantry_items_used": [string],
  "extra_items_needed": [{ "name": string, "quantity": float | null, "unit": string | null }],
  "adaptations": [string]
}

Rules:
- source_recipe: title of the candidate recipe you adapted.
- adaptations: list of changes you made (e.g. "substituted cream with milk", "omitted pine nuts").
- Prioritize pantry items expiring soon.
- from_pantry: true only if the ingredient is present in the user's inventory.
- extra_items_needed: keep minimal — adapt aggressively before saying something is missing.
- instructions: clear numbered steps reflecting the adapted recipe.
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

    supabase = get_admin_client()
    recipes = supabase.table("recipes").select("id, title, ingredients").execute().data
    return match_recipes(active_items, recipes)


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


def rag_generate_recipe(inventory: list[dict]) -> dict | None:
    """Retrieve top corpus recipes, then adapt the best match to the user's pantry."""
    active_items = [i for i in inventory if i["status"] not in ("finished", "expired")]
    if not active_items:
        return None

    supabase = get_admin_client()
    all_recipes = supabase.table("recipes").select("id, title, ingredients, instructions, cuisine").execute().data

    candidates = match_recipes(active_items, all_recipes, limit=5)
    if not candidates:
        # no corpus match — fall back to pure generation
        return generate_recipe(inventory)

    candidate_ids = {str(c["recipe_id"]) for c in candidates}
    candidate_recipes = [r for r in all_recipes if str(r["id"]) in candidate_ids]

    inventory_json = json.dumps(
        [{"name": i["name"], "category": i["category"], "status": i["status"]} for i in active_items]
    )
    candidates_json = json.dumps(candidate_recipes)

    model = _get_model(system_instruction=RAG_PROMPT)
    response = model.generate_content(
        f"My pantry:\n{inventory_json}\n\nCandidate recipes:\n{candidates_json}"
    )
    return _extract_json(response.text.strip())
