import databases
import sqlalchemy

DATABASE_URL = "sqlite+aiosqlite:///./assessment.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

payments_table = sqlalchemy.Table(
    "payments",
    metadata,
    sqlalchemy.Column("payment_id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("updated_at", sqlalchemy.Float, nullable=False),
)

idempotency_table = sqlalchemy.Table(
    "idempotency_keys",
    metadata,
    sqlalchemy.Column("key", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("request_payload", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("response_payload", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.Float, nullable=False),
)

engine = sqlalchemy.create_engine(DATABASE_URL.replace("+aiosqlite", ""), connect_args={"check_same_thread": False})


def create_tables():
    metadata.create_all(engine)
