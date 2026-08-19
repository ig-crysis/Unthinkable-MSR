from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    filename: str
    status: str
    file_size_bytes: int
    duration_seconds: float | None
    requires_chunking: bool
    processing_note: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
