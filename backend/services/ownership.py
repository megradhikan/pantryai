from fastapi import HTTPException
from services.supabase_client import get_admin_client

TABLE_OWNER_COLUMN = {
    "receipts": "user_id",
    "inventory_items": "user_id",
    "shopping_lists": "user_id",
    "push_subscriptions": "user_id",
}


def assert_owns(table: str, resource_id: str, user_id: str) -> dict:
    """
    Verifies the resource exists and belongs to user_id.
    Always returns HTTP 404 on failure — not 403.
    Reason: 403 reveals the resource exists and belongs to someone else,
    which is useful information for an attacker. 404 reveals nothing.
    Returns the full row on success so the caller can use it directly
    without a second DB fetch.
    """
    supabase = get_admin_client()
    owner_col = TABLE_OWNER_COLUMN.get(table)
    if not owner_col:
        raise ValueError(f"Table '{table}' not registered in TABLE_OWNER_COLUMN")
    result = supabase.table(table).select("*").eq("id", resource_id).execute()
    rows = result.data
    if not rows:
        raise HTTPException(status_code=404, detail="Not found")
    row = rows[0]
    if row.get(owner_col) != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    return row
