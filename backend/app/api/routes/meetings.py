from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.meeting import Meeting
from app.schemas.meeting import MeetingRead
from app.services.storage_service import UploadTooLarge, is_allowed_audio, save_upload

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("", response_model=MeetingRead, status_code=201)
def upload_meeting(
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

    meeting = Meeting(
        title=title.strip() or file.filename,
        filename=file.filename,
        audio_path=audio_path,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
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
