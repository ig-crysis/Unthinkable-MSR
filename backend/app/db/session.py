from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _normalize_url(url: str) -> str:
    # Hosted Postgres providers (Neon, Render, Heroku) hand out plain
    # `postgres://` / `postgresql://` URLs, which SQLAlchemy would route to
    # psycopg2 — point them at the psycopg (v3) driver that's actually installed.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


database_url = _normalize_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
# pool_pre_ping: serverless Postgres (Neon) suspends after idle and drops
# pooled connections; test each one on checkout instead of erroring mid-request.
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)

if database_url.startswith("sqlite"):
    # SQLite ignores foreign keys unless asked per-connection; enforce them so
    # local dev and tests catch the same constraint violations Postgres would.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
