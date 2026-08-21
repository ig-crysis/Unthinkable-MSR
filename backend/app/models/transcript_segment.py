import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _new_id() -> str:
    return uuid.uuid4().hex


class TranscriptSegment(Base):
    """One speaker turn — LLM-inferred from the flat transcript's own context
    (Whisper has no speaker identity, only text), so `speaker` is a best-effort
    label, not verified diarization. `start_seconds` is real, taken from the
    underlying Whisper segment the turn started on."""

    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    speaker: Mapped[str] = mapped_column(String(120))
    start_seconds: Mapped[float | None] = mapped_column(Float, default=None)
    text: Mapped[str] = mapped_column(Text)
