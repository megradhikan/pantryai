from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from services.auth import get_current_user
from services.supabase_client import get_admin_client
from services.rate_limiter import limiter
from services.ownership import assert_owns
from agents.inventory_agent import compute_status, SHELF_LIFE_DAYS

router = APIRouter()


@router.get("/")
@limiter.limit("120/hour")
async def list_inventory(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    items = (
        supabase.table("inventory_items")
        .select("*")
        .eq("user_id", user_id)
        .order("estimated_expiry", desc=False)
        .execute()
        .data
    )
    for item in items:
        item["status"] = compute_status(item)
    return items


@router.get("/expiring")
@limiter.limit("120/hour")
async def expiring_items(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    cutoff = (date.today() + timedelta(days=3)).isoformat()
    items = (
        supabase.table("inventory_items")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_finished", False)
        .lte("estimated_expiry", cutoff)
        .execute()
        .data
    )
    for item in items:
        item["status"] = compute_status(item)
    return items


@router.patch("/{item_id}")
@limiter.limit("60/hour")
async def update_item(
    request: Request,
    item_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    assert_owns("inventory_items", item_id, user_id)
    allowed_keys = {"quantity", "is_finished", "unit"}
    update_data = {k: v for k, v in payload.items() if k in allowed_keys}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    update_data["updated_at"] = "now()"
    supabase = get_admin_client()
    result = supabase.table("inventory_items").update(update_data).eq("id", item_id).execute()
    updated = result.data[0]
    updated["status"] = compute_status(updated)
    return updated


@router.delete("/{item_id}")
@limiter.limit("60/hour")
async def delete_item(
    request: Request,
    item_id: str,
    user_id: str = Depends(get_current_user),
):
    assert_owns("inventory_items", item_id, user_id)
    supabase = get_admin_client()
    supabase.table("inventory_items").delete().eq("id", item_id).execute()
    return {"deleted": item_id}


@router.post("/manual")
@limiter.limit("60/hour")
async def add_manual_item(
    request: Request,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    required = {"name", "category", "quantity"}
    if not required.issubset(payload.keys()):
        raise HTTPException(400, f"Missing required fields: {required - payload.keys()}")
    purchase_date = date.fromisoformat(payload.get("purchase_date", date.today().isoformat()))
    shelf_days = SHELF_LIFE_DAYS.get(payload["category"], 30)
    estimated_expiry = purchase_date + timedelta(days=shelf_days)
    supabase = get_admin_client()
    result = (
        supabase.table("inventory_items")
        .insert(
            {
                "user_id": user_id,
                "name": payload["name"],
                "category": payload["category"],
                "quantity": payload["quantity"],
                "unit": payload.get("unit"),
                "purchase_date": purchase_date.isoformat(),
                "estimated_expiry": estimated_expiry.isoformat(),
                "is_finished": False,
            }
        )
        .execute()
    )
    item = result.data[0]
    item["status"] = compute_status(item)
    return item
