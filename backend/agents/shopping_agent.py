import os
import google.generativeai as genai
from rapidfuzz import fuzz
from services.supabase_client import get_admin_client
from agents.inventory_agent import compute_status

NORMALIZE_PROMPT = """Normalize this ingredient name to its canonical grocery form.
Return ONLY the normalized name, no explanation, no punctuation.
Examples: "heavy whipping cream" → "cream", "boneless chicken breast" → "chicken breast", "fresh cilantro" → "cilantro"
"""


def _get_model():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel("gemini-2.5-flash", system_instruction=NORMALIZE_PROMPT)


def normalize_ingredient_name(name: str) -> str:
    model = _get_model()
    response = model.generate_content(name)
    return response.text.strip().lower()


def generate_shopping_list(recipe_id: str, user_id: str) -> list[dict]:
    supabase = get_admin_client()
    recipe = (
        supabase.table("recipes").select("*").eq("id", recipe_id).single().execute().data
    )
    inventory = (
        supabase.table("inventory_items")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_finished", False)
        .execute()
        .data
    )
    for item in inventory:
        item["status"] = compute_status(item)
    active_inventory = [i for i in inventory if i["status"] not in ("finished", "expired")]

    missing = []
    for ingredient in recipe["ingredients"]:
        if not ingredient.get("required", True):
            continue
        normalized = normalize_ingredient_name(ingredient["name"])
        found = False
        for inv_item in active_inventory:
            score = fuzz.partial_ratio(normalized, inv_item["name"].lower())
            if score >= 80:
                found = True
                break
        if not found:
            missing.append(
                {
                    "name": ingredient["name"],
                    "quantity": ingredient.get("quantity"),
                    "unit": ingredient.get("unit"),
                    "checked": False,
                    "category": "Other",
                }
            )

    return missing
