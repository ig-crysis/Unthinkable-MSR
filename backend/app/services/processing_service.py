"""Background pipeline: transcribe a meeting (direct or chunked map-reduce)."""

import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.meeting import STATUS_FAILED, STATUS_TRANSCRIBED, STATUS_TRANSCRIBING, Meeting
from app.models.transcript import Transcript
from app.services import asr_service, chunking_service

CHUNK_CONCURRENCY = 3


def process_meeting(meeting_id: str) -> None:
    """Entry point for FastAPI's BackgroundTasks — owns its own DB session
    since the request-scoped one is already closed by the time this runs.
    """
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return

        meeting.status = STATUS_TRANSCRIBING
        db.commit()

        try:
            if meeting.requires_chunking:
                text, language, chunk_count = _transcribe_chunked(meeting)
            else:
                result = asr_service.transcribe_file(meeting.audio_path)
                text, language, chunk_count = result["text"], result["language"], 1

            db.add(Transcript(
                meeting_id=meeting.id,
                full_text=text,
                language=language,
                provider=f"groq:{settings.asr_model}",
                chunk_count=chunk_count,
            ))
            meeting.status = STATUS_TRANSCRIBED
            meeting.error_message = None
            db.commit()
        except Exception as exc:
            db.rollback()
            meeting = db.get(Meeting, meeting_id)
            meeting.status = STATUS_FAILED
            meeting.error_message = str(exc)[:2000]
            db.commit()
    finally:
        db.close()


def _transcribe_chunked(meeting: Meeting) -> tuple[str, str | None, int]:
    chunk_dir = Path(settings.upload_dir) / "chunks" / meeting.id
    try:
        chunk_paths = chunking_service.split_audio(meeting.audio_path, chunk_dir)
        texts: list[str | None] = [None] * len(chunk_paths)
        language: str | None = None

        with ThreadPoolExecutor(max_workers=CHUNK_CONCURRENCY) as pool:
            future_to_index = {
                pool.submit(asr_service.transcribe_file, str(p)): i
                for i, p in enumerate(chunk_paths)
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                result = future.result()
                texts[index] = result["text"]
                if language is None:
                    language = result["language"]

        full_text = "\n\n".join(t for t in texts if t)
        return full_text, language, len(chunk_paths)
    finally:
        shutil.rmtree(chunk_dir, ignore_errors=True)
