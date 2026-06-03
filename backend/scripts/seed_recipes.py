"""
Run once: python scripts/seed_recipes.py
Reads recipes from data/recipes.json and seeds the recipes table with embeddings.

Recipe JSON structure:
[{
  "title": str,
  "ingredients": [{ "name": str, "quantity": float|null, "unit": str|null, "required": bool }],
  "instructions": str,
  "cuisine": str|null,
  "prep_time_mins": int|null
}]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from services.embeddings import embed_text
from services.supabase_client import get_admin_client


def build_recipe_text(recipe: dict) -> str:
    ingredient_names = " ".join(i["name"] for i in recipe["ingredients"])
    return f"{recipe['title']} {ingredient_names}"


def seed():
    supabase = get_admin_client()
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "recipes.json")
    with open(data_path) as f:
        recipes = json.load(f)
    for recipe in recipes:
        text = build_recipe_text(recipe)
        embedding = embed_text(text)
        supabase.table("recipes").insert({**recipe, "embedding": embedding}).execute()
    print(f"Seeded {len(recipes)} recipes.")


if __name__ == "__main__":
    seed()
