from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import action_items, meetings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)
app.include_router(action_items.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
