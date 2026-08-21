import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.routes import action_items, meetings
from app.db.session import Base, engine

# Without this, logger.info()/.warning() calls throughout app.services (ASR/
# diarization/summarization timing and failure diagnostics) are silently
# dropped — the root logger defaults to WARNING with no handler attached.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # `owner_id` was added to `meetings` after the table already existed in
    # deployed databases; create_all() only creates missing tables, not
    # missing columns, so patch it in by hand — no Alembic for one column.
    existing_columns = {col["name"] for col in inspect(engine).get_columns("meetings")}
    if "owner_id" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE meetings ADD COLUMN owner_id VARCHAR(64)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_meetings_owner_id ON meetings (owner_id)"))
    yield


app = FastAPI(title="Meeting Summarizer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://unthink-meetiq.centralindia.cloudapp.azure.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)
app.include_router(action_items.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
