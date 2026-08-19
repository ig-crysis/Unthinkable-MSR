from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    description: str
    owner: str | None
    due_date: str | None
    priority: str
    status: str
    order_index: int


class ActionItemUpdate(BaseModel):
    status: str | None = None
    owner: str | None = None
    due_date: str | None = None


class SummaryRead(BaseModel):
    id: str
    meeting_id: str
    overview: str
    model_used: str
    prompt_version: str
    key_decisions: list[str]
    action_items: list[ActionItemRead]
    created_at: datetime
