import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _new_id() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), unique=True)
    full_text: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16), default=None)
    provider: Mapped[str] = mapped_column(String(64))
    chunk_count: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
