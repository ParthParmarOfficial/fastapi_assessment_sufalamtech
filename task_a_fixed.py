# task_a_fixed.py — all 4 bugs fixed
import asyncio
import threading
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from databases import Database

app = FastAPI()

fake_db = {
    "products": {
        "p1": {"name": "Widget", "stock": 10}
    }
}

# FIX 2: Lock prevents race condition on stock update
_lock = threading.Lock()


# FIX 1: Now properly awaited wherever called
async def get_product(product_id: str):
    await asyncio.sleep(0)
    return fake_db["products"].get(product_id)


@app.post("/order/{product_id}")
async def place_order(product_id: str):
    product = await get_product(product_id)  # FIX 1: await added

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    with _lock:  # FIX 2: atomic check-and-update
        if product["stock"] <= 0:
            raise HTTPException(status_code=400, detail="Out of stock")
        product["stock"] -= 1

    return {"status": "ordered", "remaining_stock": product["stock"]}


# FIX 3: Parameterized query — no SQL injection possible
async def get_user(username: str, db: Database):
    query = text("SELECT * FROM users WHERE username = :username")
    return await db.fetch_one(query, values={"username": username})


# FIX 4: Proper 404 + error handling
@app.get("/product/{product_id}")
async def fetch_product(product_id: str):
    product = fake_db["products"].get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": product}