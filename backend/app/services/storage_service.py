import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".aac"}


def is_allowed_audio(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


class UploadTooLarge(Exception):
    pass


def save_upload(file: UploadFile) -> str:
    """Streams the upload to disk under a random name; returns the stored path.

    Raises UploadTooLarge (and removes the partial file) if the stream exceeds
    settings.max_upload_mb before it finishes.
    """
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    dest = upload_dir / f"{uuid.uuid4().hex}{ext}"
    max_bytes = settings.max_upload_mb * 1024 * 1024

    written = 0
    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise UploadTooLarge(f"Upload exceeds {settings.max_upload_mb}MB limit.")
            out.write(chunk)

    return str(dest)
