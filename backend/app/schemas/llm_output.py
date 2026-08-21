"""Validates the raw JSON the LLM returns before it's trusted and persisted."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ActionItemOut(BaseModel):
    description: str
    owner: str | None = None
    due_date: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"

    @field_validator("priority", mode="before")
    @classmethod
    def _default_missing_priority(cls, value: object) -> object:
        # A field default only applies when the key is absent — the LLM
        # sometimes emits an explicit `"priority": null` instead of omitting
        # it, or "medium" isn't returned but wasn't a recognized string.
        return value if value in ("low", "medium", "high") else "medium"


class SummaryOut(BaseModel):
    overview: str
    key_decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItemOut] = Field(default_factory=list)
