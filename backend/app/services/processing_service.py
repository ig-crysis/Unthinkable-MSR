"""Background pipeline: transcribe a meeting (direct or chunked map-reduce)."""

import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.action_item import ActionItem
from app.models.key_decision import KeyDecision
from app.models.meeting import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_SUMMARIZING,
    STATUS_TRANSCRIBED,
    STATUS_TRANSCRIBING,
    Meeting,
)
from app.models.summary import Summary
from app.models.transcript import Transcript
from app.services import asr_service, chunking_service, llm_service

CHUNK_CONCURRENCY = 3


def process_meeting(meeting_id: str) -> None:
    """Entry point for FastAPI's BackgroundTasks — owns its own DB session
    since the request-scoped one is already closed by the time this runs.
    Runs transcription then summarization as one pipeline; either stage's
    failure lands the meeting in STATUS_FAILED with a descriptive message.
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
            meeting.error_message = f"Transcription failed: {str(exc)[:1900]}"
            db.commit()
            return

        try:
            meeting.status = STATUS_SUMMARIZING
            db.commit()

            summary_out, prompt_version = llm_service.summarize_transcript(
                text, two_pass=meeting.requires_chunking
            )

            summary = Summary(
                meeting_id=meeting.id,
                overview=summary_out.overview,
                model_used=settings.llm_model,
                prompt_version=prompt_version,
            )
            db.add(summary)
            db.flush()  # assigns summary.id for the FK rows below

            for i, decision_text in enumerate(summary_out.key_decisions):
                db.add(KeyDecision(summary_id=summary.id, decision_text=decision_text, order_index=i))

            for i, item in enumerate(summary_out.action_items):
                db.add(ActionItem(
                    summary_id=summary.id,
                    description=item.description,
                    owner=item.owner,
                    due_date=item.due_date,
                    priority=item.priority,
                    order_index=i,
                ))

            meeting.status = STATUS_COMPLETED
            meeting.error_message = None
            db.commit()
        except Exception as exc:
            db.rollback()
            meeting = db.get(Meeting, meeting_id)
            meeting.status = STATUS_FAILED
            meeting.error_message = f"Summarization failed: {str(exc)[:1900]}"
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
