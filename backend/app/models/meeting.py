import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# "pending_confirmation" is a distinct status from "uploaded": it means the
# file is stored and sized, but processing is withheld until the user
# explicitly accepts the chunked-processing time cost (see routes/meetings.py).
STATUS_UPLOADED = "uploaded"
STATUS_PENDING_CONFIRMATION = "pending_confirmation"
STATUS_TRANSCRIBING = "transcribing"
STATUS_TRANSCRIBED = "transcribed"
STATUS_FAILED = "failed"


def _new_id() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[int] = mapped_column(default=0)
    duration_seconds: Mapped[float | None] = mapped_column(default=None)
    requires_chunking: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default=STATUS_UPLOADED)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    @property
    def processing_note(self) -> str | None:
        """Human-readable reason shown to the user when confirmation is required."""
        if self.status != STATUS_PENDING_CONFIRMATION:
            return None
        if self.duration_seconds:
            minutes = round(self.duration_seconds / 60)
            return (
                f"This meeting is about {minutes} min long, so it will be split into "
                "chunks and processed in the background — this may take a few minutes. Continue?"
            )
        size_mb = round(self.file_size_bytes / (1024 * 1024), 1)
        return (
            f"This file is {size_mb}MB, so it will be split into chunks and processed "
            "in the background — this may take a few minutes. Continue?"
        )
