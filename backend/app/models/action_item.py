import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

STATUS_OPEN = "open"
STATUS_DONE = "done"


def _new_id() -> str:
    return uuid.uuid4().hex


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    summary_id: Mapped[str] = mapped_column(ForeignKey("summaries.id"))
    description: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(120), default=None)
    due_date: Mapped[str | None] = mapped_column(String(32), default=None)
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    status: Mapped[str] = mapped_column(String(16), default=STATUS_OPEN)
    order_index: Mapped[int] = mapped_column(default=0)
