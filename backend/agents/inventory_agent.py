from datetime import date, timedelta, datetime
from rapidfuzz import fuzz
from services.supabase_client import get_admin_client

SHELF_LIFE_DAYS = {
    "Dairy": 10,
    "Protein": 3,
    "Produce": 5,
    "Grains": 180,
    "Snacks": 60,
    "Beverages": 14,
    "Frozen": 90,
    "Condiments": 180,
    "Other": 30,
}


def compute_status(item: dict) -> str:
    """Computes display status. Never stored in DB."""
    if item["is_finished"]:
        return "finished"
    today = date.today()
    expiry = item["estimated_expiry"]
    if isinstance(expiry, str):
        expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
    if today > expiry:
        return "expired"
    if today >= expiry - timedelta(days=2):
        return "expiring_soon"
    if item["quantity"] <= 1:
        return "low"
    return "fresh"


def find_existing_item(user_id: str, normalized_name: str, existing_items: list[dict]) -> dict | None:
    for item in existing_items:
        if item["name"].lower() == normalized_name.lower():
            return item
    for item in existing_items:
        score = fuzz.ratio(item["name"].lower(), normalized_name.lower())
        if score >= 85:
            return item
    return None


async def upsert_items(user_id: str, items: list, purchase_date: date, receipt_id: str):
    supabase = get_admin_client()
    existing = (
        supabase.table("inventory_items")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_finished", False)
        .execute()
        .data
    )

    for item in items:
        shelf_days = SHELF_LIFE_DAYS.get(item.category, 30)
        estimated_expiry = purchase_date + timedelta(days=shelf_days)
        match = find_existing_item(user_id, item.name, existing)

        if match:
            supabase.table("inventory_items").update(
                {"quantity": match["quantity"] + item.quantity, "updated_at": "now()"}
            ).eq("id", match["id"]).execute()
        else:
            supabase.table("inventory_items").insert(
                {
                    "user_id": user_id,
                    "name": item.name,
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "purchase_date": purchase_date.isoformat(),
                    "estimated_expiry": estimated_expiry.isoformat(),
                    "is_finished": False,
                    "receipt_id": receipt_id,
                }
            ).execute()
