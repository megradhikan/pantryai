import re
from difflib import SequenceMatcher


def _tokens(name: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", name.lower())
    normalized = set()
    for word in words:
        if len(word) > 3 and word.endswith("ies"):
            word = f"{word[:-3]}y"
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        normalized.add(word)
    return normalized


def ingredient_matches(ingredient_name: str, pantry_name: str) -> bool:
    """Match common receipt variations without loading an ML model."""
    ingredient_tokens = _tokens(ingredient_name)
    pantry_tokens = _tokens(pantry_name)
    if not ingredient_tokens or not pantry_tokens:
        return False

    # Covers useful equivalents such as "chicken"/"chicken breast" and
    # "milk"/"almond milk" while avoiding raw substring false positives.
    if ingredient_tokens <= pantry_tokens or pantry_tokens <= ingredient_tokens:
        return True

    ingredient_text = " ".join(sorted(ingredient_tokens))
    pantry_text = " ".join(sorted(pantry_tokens))
    return SequenceMatcher(None, ingredient_text, pantry_text).ratio() >= 0.84


def match_recipes(
    inventory: list[dict], recipes: list[dict], limit: int = 5
) -> list[dict]:
    active_items = [
        item for item in inventory if item.get("status") not in ("finished", "expired")
    ]
    if not active_items:
        return []

    ranked = []
    for recipe in recipes:
        ingredients = recipe.get("ingredients") or []
        required = [ingredient for ingredient in ingredients if ingredient.get("required", True)]
        matched_required = 0
        expiring_matches = 0
        used_names: list[str] = []
        missing = []

        for ingredient in ingredients:
            pantry_item = next(
                (
                    item
                    for item in active_items
                    if ingredient_matches(ingredient.get("name", ""), item.get("name", ""))
                ),
                None,
            )
            if pantry_item:
                pantry_name = pantry_item["name"]
                if pantry_name not in used_names:
                    used_names.append(pantry_name)
                if ingredient.get("required", True):
                    matched_required += 1
                if pantry_item.get("status") == "expiring_soon":
                    expiring_matches += 1
            elif ingredient.get("required", True):
                missing.append(
                    {
                        "name": ingredient.get("name", ""),
                        "quantity": ingredient.get("quantity"),
                        "unit": ingredient.get("unit"),
                    }
                )

        match_score = matched_required / len(required) if required else 1.0
        ranked.append(
            {
                "recipe_id": str(recipe["id"]),
                "title": recipe["title"],
                "inventory_items_used": used_names,
                "missing_ingredients": missing,
                "match_score": round(match_score, 4),
                "_expiring_matches": expiring_matches,
            }
        )

    ranked.sort(
        key=lambda recipe: (
            -recipe["match_score"],
            -recipe["_expiring_matches"],
            -len(recipe["inventory_items_used"]),
            recipe["title"].lower(),
        )
    )
    for recipe in ranked:
        recipe.pop("_expiring_matches")
    return ranked[:limit]
