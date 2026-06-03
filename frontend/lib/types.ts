export interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string | null;
  purchase_date: string;
  estimated_expiry: string;
  is_finished: boolean;
  status: "fresh" | "low" | "expiring_soon" | "expired" | "finished";
  receipt_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ExtractedItem {
  name: string;
  quantity: number;
  unit: string | null;
  category: string;
}

export interface UploadReceiptResponse {
  receipt_id: string;
  store_name: string | null;
  purchase_date: string;
  items: ExtractedItem[];
  metadata: {
    ocr_engine: string;
    confidence: number | null;
    item_count: number;
    parse_success: boolean;
  };
}

export interface EvalSummary {
  total_receipts?: number;
  total?: number;
  parse_success_rate?: number;
  avg_items_per_receipt?: number;
  ocr_engine_breakdown?: { google: number; tesseract: number };
}

export interface RecipeSuggestion {
  recipe_id: string;
  title: string;
  inventory_items_used: string[];
  missing_ingredients: { name: string; quantity: number | null; unit: string | null }[];
  match_score: number;
}

export interface ShoppingList {
  id: string;
  user_id: string;
  recipe_id: string;
  recipe_title: string;
  items: ShoppingItem[];
  created_at: string;
}

export interface ShoppingItem {
  name: string;
  quantity: number | null;
  unit: string | null;
  checked: boolean;
  category: string;
}

export interface ManualItemPayload {
  name: string;
  category: string;
  quantity: number;
  unit?: string;
  purchase_date?: string;
}

export interface PushSubscriptionData {
  endpoint: string;
  p256dh: string;
  auth: string;
}

export interface Receipt {
  id: string;
  store_name: string | null;
  purchase_date: string;
  extracted_items: ExtractedItem[] | null;
  extraction_metadata: {
    item_count: number;
    ocr_engine: string;
    parse_success: boolean;
  } | null;
  created_at: string;
}
