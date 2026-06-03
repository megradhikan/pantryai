from fastapi import APIRouter, Depends, HTTPException, Request
from services.auth import get_current_user
from services.supabase_client import get_admin_client
from services.rate_limiter import limiter
from services.ownership import assert_owns
from agents.shopping_agent import generate_shopping_list

router = APIRouter()


@router.post("/generate")
@limiter.limit("30/hour")
async def create_shopping_list(
    request: Request,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    recipe_id = payload.get("recipe_id")
    if not recipe_id:
        raise HTTPException(400, "recipe_id required")

    supabase = get_admin_client()
    recipe = (
        supabase.table("recipes").select("title").eq("id", recipe_id).single().execute().data
    )
    missing_items = generate_shopping_list(recipe_id, user_id)

    if not missing_items:
        return {"message": "You have all ingredients!", "items": []}

    result = (
        supabase.table("shopping_lists")
        .insert(
            {
                "user_id": user_id,
                "recipe_id": recipe_id,
                "recipe_title": recipe["title"],
                "items": missing_items,
            }
        )
        .execute()
        .data[0]
    )

    # Mark the most recent suggestion log entry
    logs = supabase.table("recipe_suggestion_log").select("id").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute().data
    if logs:
        supabase.table("recipe_suggestion_log").update({"led_to_shopping_list": True}).eq("id", logs[0]["id"]).execute()

    return result


@router.post("/create")
@limiter.limit("30/hour")
async def create_custom_shopping_list(
    request: Request,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    """Create a shopping list from arbitrary items (for AI-generated recipes)."""
    title = payload.get("title", "Shopping List")
    items = payload.get("items", [])
    if not items:
        raise HTTPException(400, "items required")

    shopping_items = [
        {
            "name": i.get("name", ""),
            "quantity": i.get("quantity"),
            "unit": i.get("unit"),
            "checked": False,
            "category": i.get("category", "Other"),
        }
        for i in items
        if i.get("name")
    ]

    supabase = get_admin_client()
    result = (
        supabase.table("shopping_lists")
        .insert(
            {
                "user_id": user_id,
                "recipe_id": None,
                "recipe_title": title,
                "items": shopping_items,
            }
        )
        .execute()
        .data[0]
    )
    return result


@router.get("/")
@limiter.limit("120/hour")
async def get_shopping_lists(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    return (
        supabase.table("shopping_lists")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
        .data
    )


@router.patch("/{list_id}/item")
@limiter.limit("120/hour")
async def toggle_item(
    request: Request,
    list_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    lst = assert_owns("shopping_lists", list_id, user_id)
    item_name = payload.get("item_name")
    if not item_name:
        raise HTTPException(status_code=400, detail="item_name required")
    items = lst["items"]
    for item in items:
        if item["name"] == item_name:
            item["checked"] = not item["checked"]
            break
    supabase = get_admin_client()
    supabase.table("shopping_lists").update({"items": items}).eq("id", list_id).execute()
    return {"items": items}
