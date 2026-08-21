from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranscriptSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    speaker: str
    start_seconds: float | None
    text: str


class TranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meeting_id: str
    full_text: str
    language: str | None
    provider: str
    chunk_count: int
    created_at: datetime
    segments: list[TranscriptSegmentRead] = []
