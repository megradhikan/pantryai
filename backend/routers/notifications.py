from fastapi import APIRouter, Depends, Request
from services.auth import get_current_user
from services.supabase_client import get_admin_client
from services.rate_limiter import limiter

router = APIRouter()


@router.post("/subscribe")
@limiter.limit("5/hour")
async def subscribe(
    request: Request,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    supabase.table("push_subscriptions").upsert(
        {
            "user_id": user_id,
            "endpoint": payload["endpoint"],
            "p256dh": payload["p256dh"],
            "auth": payload["auth"],
        },
        on_conflict="endpoint",
    ).execute()
    return {"subscribed": True}
