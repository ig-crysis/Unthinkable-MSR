"""Groq-hosted Whisper transcription (OpenAI-compatible SDK, Groq's endpoint)."""

import time

from groq import Groq

from app.core.config import settings

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set — add it to backend/.env")
        # The SDK's own default (60s read timeout, 2 internal retries) stacks
        # on top of this module's own retry loop below — a single slow
        # response can silently cascade into minutes of nested retries.
        # max_retries=0 here makes our explicit loop the only retry layer.
        _client = Groq(api_key=settings.groq_api_key, timeout=45.0, max_retries=0)
    return _client


def _seg_get(seg, key, default=None):
    """Groq's SDK may hand back segments as objects or plain dicts depending
    on version — read either way rather than assuming."""
    if isinstance(seg, dict):
        return seg.get(key, default)
    return getattr(seg, key, default)


def transcribe_file(path: str, max_attempts: int = 3) -> dict:
    """Returns {"text": str, "language": str | None, "segments": [{"start", "end", "text"}]}.
    Segments have real Whisper timestamps but no speaker identity — Whisper
    doesn't diarize. Retries transient failures (rate limits, timeouts) with a
    short backoff before giving up.
    """
    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with open(path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=(path, audio_file.read()),
                    model=settings.asr_model,
                    response_format="verbose_json",
                )
            raw_segments = getattr(response, "segments", None) or []
            segments = [
                {
                    "start": float(_seg_get(seg, "start", 0.0)),
                    "end": float(_seg_get(seg, "end", 0.0)),
                    "text": (_seg_get(seg, "text", "") or "").strip(),
                }
                for seg in raw_segments
                if (_seg_get(seg, "text", "") or "").strip()
            ]
            return {
                "text": (response.text or "").strip(),
                "language": getattr(response, "language", None),
                "segments": segments,
            }
        except Exception as exc:  # Groq SDK raises several distinct error types
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2**attempt)

    raise RuntimeError(f"Transcription failed after {max_attempts} attempts: {last_error}") from last_error
