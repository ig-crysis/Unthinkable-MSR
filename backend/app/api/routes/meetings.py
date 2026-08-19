from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.action_item import ActionItem
from app.models.key_decision import KeyDecision
from app.models.meeting import STATUS_PENDING_CONFIRMATION, STATUS_UPLOADED, Meeting
from app.models.summary import Summary
from app.models.transcript import Transcript
from app.schemas.meeting import MeetingRead
from app.schemas.summary import ActionItemRead, SummaryRead
from app.schemas.transcript import TranscriptRead
from app.services import chunking_service
from app.services.processing_service import process_meeting
from app.services.storage_service import UploadTooLarge, is_allowed_audio, save_upload

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("", response_model=MeetingRead, status_code=201)
def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(default=""),
    db: Session = Depends(get_db),
) -> Meeting:
    if not file.filename or not is_allowed_audio(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported audio file type.")

    try:
        audio_path = save_upload(file)
    except UploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    file_size_bytes = Path(audio_path).stat().st_size
    duration_seconds = chunking_service.get_duration_seconds(audio_path)
    requires_chunking = chunking_service.needs_chunking(file_size_bytes, duration_seconds)

    meeting = Meeting(
        title=title.strip() or file.filename,
        filename=file.filename,
        audio_path=audio_path,
        file_size_bytes=file_size_bytes,
        duration_seconds=duration_seconds,
        requires_chunking=requires_chunking,
        status=STATUS_PENDING_CONFIRMATION if requires_chunking else STATUS_UPLOADED,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    if not requires_chunking:
        background_tasks.add_task(process_meeting, meeting.id)

    return meeting


@router.post("/{meeting_id}/confirm-processing", response_model=MeetingRead)
def confirm_processing(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    if meeting.status != STATUS_PENDING_CONFIRMATION:
        raise HTTPException(status_code=409, detail=f"Meeting is not awaiting confirmation (status: {meeting.status}).")

    meeting.status = STATUS_UPLOADED
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting.id)
    return meeting


@router.get("", response_model=list[MeetingRead])
def list_meetings(db: Session = Depends(get_db)) -> list[Meeting]:
    return list(db.execute(select(Meeting).order_by(Meeting.created_at.desc())).scalars().all())


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting


@router.get("/{meeting_id}/transcript", response_model=TranscriptRead)
def get_transcript(meeting_id: str, db: Session = Depends(get_db)) -> Transcript:
    transcript = db.execute(
        select(Transcript).where(Transcript.meeting_id == meeting_id)
    ).scalar_one_or_none()
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not available yet.")
    return transcript


@router.get("/{meeting_id}/summary", response_model=SummaryRead)
def get_summary(meeting_id: str, db: Session = Depends(get_db)) -> SummaryRead:
    summary = db.execute(
        select(Summary).where(Summary.meeting_id == meeting_id)
    ).scalar_one_or_none()
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not available yet.")

    decisions = db.execute(
        select(KeyDecision).where(KeyDecision.summary_id == summary.id).order_by(KeyDecision.order_index)
    ).scalars().all()
    action_items = db.execute(
        select(ActionItem).where(ActionItem.summary_id == summary.id).order_by(ActionItem.order_index)
    ).scalars().all()

    return SummaryRead(
        id=summary.id,
        meeting_id=summary.meeting_id,
        overview=summary.overview,
        model_used=summary.model_used,
        prompt_version=summary.prompt_version,
        key_decisions=[d.decision_text for d in decisions],
        action_items=[ActionItemRead.model_validate(ai) for ai in action_items],
        created_at=summary.created_at,
    )
