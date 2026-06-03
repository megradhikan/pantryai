from fastapi import APIRouter, Depends, Request
from services.auth import get_current_user
from services.supabase_client import get_admin_client
from services.rate_limiter import limiter
from agents.recipe_agent import suggest_recipes, generate_recipe
from agents.inventory_agent import compute_status

router = APIRouter()


@router.get("/suggest")
@limiter.limit("30/hour")
async def get_suggestions(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    inventory = (
        supabase.table("inventory_items").select("*").eq("user_id", user_id).execute().data
    )
    for item in inventory:
        item["status"] = compute_status(item)

    suggestions = suggest_recipes(inventory)

    if suggestions:
        avg_score = sum(s["match_score"] for s in suggestions) / len(suggestions)
        supabase.table("recipe_suggestion_log").insert(
            {
                "user_id": user_id,
                "suggested_recipe_ids": [s["recipe_id"] for s in suggestions],
                "avg_match_score": avg_score,
                "led_to_shopping_list": False,
            }
        ).execute()

    return {"suggestions": suggestions}


@router.get("/generate")
@limiter.limit("20/hour")
async def get_generated_recipe(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    inventory = (
        supabase.table("inventory_items").select("*").eq("user_id", user_id).execute().data
    )
    for item in inventory:
        item["status"] = compute_status(item)

    recipe = generate_recipe(inventory)
    return {"recipe": recipe}


@router.get("/eval")
@limiter.limit("60/hour")
async def get_eval(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    logs = supabase.table("recipe_suggestion_log").select("*").execute().data
    if not logs:
        return {
            "avg_match_score": 0,
            "total_suggestions": 0,
            "led_to_shopping_list_pct": 0,
            "top_recipes": [],
        }

    total = len(logs)
    avg_score = sum(l["avg_match_score"] or 0 for l in logs) / total
    led = sum(1 for l in logs if l["led_to_shopping_list"])

    from collections import Counter

    recipe_counts: Counter = Counter()
    for log in logs:
        for rid in log["suggested_recipe_ids"]:
            recipe_counts[rid] += 1

    top_ids = [r for r, _ in recipe_counts.most_common(5)]
    top_recipes = []
    if top_ids:
        recipes = (
            supabase.table("recipes").select("id, title").in_("id", top_ids).execute().data
        )
        id_to_title = {str(r["id"]): r["title"] for r in recipes}
        top_recipes = [
            {"title": id_to_title.get(rid, rid), "count": recipe_counts[rid]}
            for rid in top_ids
        ]

    return {
        "avg_match_score": round(avg_score, 3),
        "total_suggestions": total,
        "led_to_shopping_list_pct": round(led / total, 3),
        "top_recipes": top_recipes,
    }
