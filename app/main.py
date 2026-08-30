import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import database, create_tables
from app.routes import payments, webhooks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(
    title="FastAPI Practical Assessment",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(payments.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}