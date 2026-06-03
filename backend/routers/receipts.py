import uuid
from datetime import date
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from services.auth import get_current_user
from services.ocr import run_ocr
from services.supabase_client import get_admin_client
from services.rate_limiter import limiter
from services.ownership import assert_owns
from agents.receipt_agent import extract_items
from agents.inventory_agent import upsert_items
from models.schemas import ExtractedItem

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
@limiter.limit("10/hour")
async def upload_receipt(
    request: Request,
    file: UploadFile = File(...),
    purchase_date: date = Form(default=None),
    user_id: str = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "File must be JPEG, PNG, WebP, or PDF")
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File exceeds 10MB limit")
    if purchase_date is None:
        purchase_date = date.today()

    supabase = get_admin_client()
    file_ext = (file.filename or "jpg").split(".")[-1].lower()
    storage_path = f"receipts/{user_id}/{uuid.uuid4()}.{file_ext}"
    supabase.storage.from_("receipts").upload(
        storage_path, file_bytes, {"content-type": file.content_type}
    )

    ocr_text, engine, confidence = run_ocr(file_bytes, file.content_type)
    items, store_name, metadata = extract_items(ocr_text)
    metadata.ocr_engine = engine
    if confidence is not None:
        metadata.confidence = confidence

    receipt = (
        supabase.table("receipts")
        .insert(
            {
                "user_id": user_id,
                "storage_path": storage_path,
                "raw_ocr_text": ocr_text,
                "store_name": store_name,
                "purchase_date": purchase_date.isoformat(),
                "extracted_items": [i.model_dump() for i in items],
                "extraction_metadata": metadata.model_dump(),
            }
        )
        .execute()
        .data[0]
    )

    return {
        "receipt_id": receipt["id"],
        "store_name": store_name,
        "purchase_date": purchase_date.isoformat(),
        "items": [i.model_dump() for i in items],
        "metadata": metadata.model_dump(),
    }


@router.post("/{receipt_id}/confirm")
@limiter.limit("10/hour")
async def confirm_receipt(
    request: Request,
    receipt_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    receipt_row = assert_owns("receipts", receipt_id, user_id)
    items_raw = payload.get("items", [])
    extracted = [ExtractedItem(**i) for i in items_raw]
    purchase_date = date.fromisoformat(receipt_row["purchase_date"])

    supabase = get_admin_client()
    supabase.table("receipts").update(
        {"extracted_items": [i.model_dump() for i in extracted]}
    ).eq("id", receipt_id).execute()

    await upsert_items(user_id, extracted, purchase_date, receipt_id)
    return {"confirmed": True, "item_count": len(extracted)}


@router.get("/")
@limiter.limit("120/hour")
async def list_receipts(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    return (
        supabase.table("receipts")
        .select("id, store_name, purchase_date, extracted_items, extraction_metadata, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


@router.get("/eval-summary")
@limiter.limit("60/hour")
async def eval_summary(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    supabase = get_admin_client()
    receipts = (
        supabase.table("receipts")
        .select("extraction_metadata")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    if not receipts:
        return {"total": 0}
    total = len(receipts)
    parsed = [
        r
        for r in receipts
        if r["extraction_metadata"] and r["extraction_metadata"].get("parse_success")
    ]
    parse_rate = len(parsed) / total
    avg_items = (
        sum(r["extraction_metadata"]["item_count"] for r in parsed) / max(len(parsed), 1)
    )
    google_count = sum(
        1
        for r in receipts
        if r["extraction_metadata"]
        and r["extraction_metadata"].get("ocr_engine") == "google"
    )
    return {
        "total_receipts": total,
        "parse_success_rate": round(parse_rate, 3),
        "avg_items_per_receipt": round(avg_items, 1),
        "ocr_engine_breakdown": {"google": google_count, "tesseract": total - google_count},
    }
