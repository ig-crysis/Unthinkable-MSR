"""Validates the raw JSON the LLM returns before it's trusted and persisted."""

from typing import Literal

from pydantic import BaseModel, Field


class ActionItemOut(BaseModel):
    description: str
    owner: str | None = None
    due_date: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"


class SummaryOut(BaseModel):
    overview: str
    key_decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItemOut] = Field(default_factory=list)
