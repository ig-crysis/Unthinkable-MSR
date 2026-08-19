"""Groq-hosted Llama summarization — key decisions + action items as structured JSON.

Strategy selection (see app/prompts/v1.py for the full rationale/prompt text):
- single-pass for short meetings
- two-pass extract-then-structure for meetings that went through chunked ASR
"""

import json
import time

from groq import Groq
from pydantic import ValidationError

from app.core.config import settings
from app.prompts import v1 as prompts
from app.schemas.llm_output import SummaryOut

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set — add it to backend/.env")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _chat_text(system: str, user: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()


def _chat_json(system: str, user: str, max_attempts: int = 3) -> dict:
    client = _get_client()
    prompt_user = user
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt_user}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except (json.JSONDecodeError, Exception) as exc:
            last_error = exc
            if attempt < max_attempts:
                prompt_user = user + prompts.RETRY_SUFFIX
                time.sleep(2**attempt)

    raise RuntimeError(f"LLM call did not return valid JSON after {max_attempts} attempts: {last_error}") from last_error


def summarize_transcript(transcript_text: str, two_pass: bool) -> tuple[SummaryOut, str]:
    if two_pass:
        candidates = _chat_text(prompts.EXTRACT_SYSTEM, prompts.EXTRACT_USER.format(transcript=transcript_text))
        raw = _chat_json(prompts.STRUCTURE_SYSTEM, prompts.STRUCTURE_FROM_CANDIDATES_USER.format(candidates=candidates))
        prompt_version = prompts.VERSION_TWO_PASS
    else:
        raw = _chat_json(prompts.STRUCTURE_SYSTEM, prompts.SINGLE_PASS_USER.format(transcript=transcript_text))
        prompt_version = prompts.VERSION_SINGLE_PASS

    try:
        summary_out = SummaryOut.model_validate(raw)
    except ValidationError as exc:
        raise RuntimeError(f"LLM JSON failed schema validation: {exc}") from exc

    return summary_out, prompt_version
