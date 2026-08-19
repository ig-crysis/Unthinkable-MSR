import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _new_id() -> str:
    return uuid.uuid4().hex


class KeyDecision(Base):
    __tablename__ = "key_decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    summary_id: Mapped[str] = mapped_column(ForeignKey("summaries.id"))
    decision_text: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(default=0)
