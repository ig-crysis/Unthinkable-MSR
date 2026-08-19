from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meeting_id: str
    full_text: str
    language: str | None
    provider: str
    chunk_count: int
    created_at: datetime
