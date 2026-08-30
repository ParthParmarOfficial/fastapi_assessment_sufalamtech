import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import database, create_tables, payments_table, idempotency_table


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables once, wipe data before each test for isolation."""
    create_tables()
    await database.connect()
    # Clear all tables before each test
    await database.execute(payments_table.delete())
    await database.execute(idempotency_table.delete())
    yield
    await database.disconnect()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
