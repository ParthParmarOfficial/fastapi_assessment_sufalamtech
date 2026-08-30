# task_a_buggy.py — intentionally buggy code (DO NOT USE)
import asyncio
from fastapi import FastAPI

app = FastAPI()

# Simulated in-memory DB
fake_db = {
    "products": {
        "p1": {"name": "Widget", "stock": 10}
    }
}

# BUG 1: Missing await — get_product is async but not awaited
async def get_product(product_id: str):
    await asyncio.sleep(0)  # simulates async DB call
    return fake_db["products"].get(product_id)


# BUG 2: Race condition — stock check and update not atomic
@app.post("/order/{product_id}")
async def place_order(product_id: str):
    product = get_product(product_id)  # BUG 1: missing await
    if product["stock"] > 0:
        # Another request can slip in here between check and update
        product["stock"] -= 1  # BUG 2: race condition
        return {"status": "ordered"}
    return {"status": "out of stock"}


# BUG 3: SQL injection — user input directly in query string
async def get_user(username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"  # BUG 3: injectable
    # attacker passes: ' OR '1'='1 → dumps entire table
    return query


# BUG 4: Wrong status code + no error handling
@app.get("/product/{product_id}")
async def fetch_product(product_id: str):
    product = fake_db["products"].get(product_id)
    return {"product": product}  # BUG 4: returns 200 with None if not found, no 404