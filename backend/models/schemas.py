from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid


class ExtractedItem(BaseModel):
    name: str
    quantity: float = 1.0
    unit: Optional[str] = None
    category: str


class ExtractionMetadata(BaseModel):
    ocr_engine: str
    confidence: Optional[float] = None
    item_count: int
    parse_success: bool


class InventoryItem(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    quantity: float
    unit: Optional[str]
    purchase_date: date
    estimated_expiry: date
    is_finished: bool
    status: str  # computed: fresh|low|expiring_soon|expired|finished


class RecipeIngredient(BaseModel):
    name: str
    quantity: Optional[float]
    unit: Optional[str]
    required: bool = True


class Recipe(BaseModel):
    id: uuid.UUID
    title: str
    ingredients: list[RecipeIngredient]
    instructions: str
    cuisine: Optional[str]
    prep_time_mins: Optional[int]


class RecipeSuggestion(BaseModel):
    recipe_id: str
    title: str
    inventory_items_used: list[str]
    missing_ingredients: list[dict]
    match_score: float


class ShoppingItem(BaseModel):
    name: str
    quantity: Optional[float]
    unit: Optional[str]
    checked: bool = False
    category: str


class ManualItemPayload(BaseModel):
    name: str
    category: str
    quantity: float
    unit: Optional[str] = None
    purchase_date: Optional[str] = None
