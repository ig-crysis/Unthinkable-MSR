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
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def transcribe_file(path: str, max_attempts: int = 3) -> dict:
    """Returns {"text": str, "language": str | None}. Retries transient failures
    (rate limits, timeouts) with a short backoff before giving up.
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
            return {
                "text": (response.text or "").strip(),
                "language": getattr(response, "language", None),
            }
        except Exception as exc:  # Groq SDK raises several distinct error types
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2**attempt)

    raise RuntimeError(f"Transcription failed after {max_attempts} attempts: {last_error}") from last_error
