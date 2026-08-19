import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _new_id() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), unique=True)
    overview: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
