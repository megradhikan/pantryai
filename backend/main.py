from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from services.rate_limiter import limiter
from routers import receipts, inventory, recipes, shopping, notifications

app = FastAPI(title="PantryAI")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
app.include_router(shopping.router, prefix="/api/shopping", tags=["shopping"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])


@app.get("/health")
async def health():
    return {"status": "ok"}
