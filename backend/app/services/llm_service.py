"""Groq-hosted Llama summarization — key decisions + action items as structured JSON.

Strategy selection (see app/prompts/v1.py for the full rationale/prompt text):
- single-pass for short meetings
- two-pass extract-then-structure for meetings that went through chunked ASR
  or whose transcript text alone is long enough to need it (see
  MAX_SINGLE_CALL_CHARS)
"""

import json
import logging
import time

from groq import Groq
from pydantic import ValidationError

from app.core.config import settings
from app.prompts import v1 as prompts
from app.schemas.llm_output import SummaryOut

logger = logging.getLogger(__name__)

_client: Groq | None = None
_client_diarize: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set — add it to backend/.env")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _get_diarize_client() -> Groq:
    """A second Groq account's client, used only for diarization batch
    calls so that (high-volume) workload has its own separate rate-limit
    budget. Falls back to the primary client when no second key is set."""
    global _client_diarize
    if not settings.groq_api_key_diarize:
        return _get_client()
    if _client_diarize is None:
        _client_diarize = Groq(api_key=settings.groq_api_key_diarize)
    return _client_diarize


# openai/gpt-oss-120b is a reasoning model — it burns completion tokens on a
# hidden chain-of-thought before ever writing the visible answer. Without
# reasoning_effort pinned down it can exhaust its budget mid-thought
# (sometimes visibly looping on a repeated phrase) and return empty content
# with finish_reason="length".
#
# Separately, this Groq account's tokens-per-minute cap (8000 TPM, verified
# against a real ~25-minute meeting) is charged against prompt_tokens PLUS
# the full max_completion_tokens reservation, not actual usage — so a single
# call combining a long transcript with a generous completion budget blows
# the limit outright regardless of what the model ends up using. The fix is
# keeping each individual call's own input small (batching long transcripts/
# segment lists) rather than trying to shave the completion reservation,
# since that reservation is also what prevents the empty-content failure
# above.
DEFAULT_MAX_COMPLETION_TOKENS = 6000


def _chat_text(
    system: str,
    user: str,
    max_attempts: int = 2,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
    client: Groq | None = None,
) -> str:
    client = client or _get_client()
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                reasoning_effort="low",
                max_completion_tokens=max_completion_tokens,
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
            last_error = RuntimeError(f"LLM returned empty content (finish_reason={response.choices[0].finish_reason})")
        except Exception as exc:
            last_error = exc
        if attempt < max_attempts:
            time.sleep(2**attempt)

    raise RuntimeError(f"LLM call returned no usable content after {max_attempts} attempts: {last_error}") from last_error


def _chat_json(
    system: str,
    user: str,
    max_attempts: int = 3,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
    client: Groq | None = None,
) -> dict:
    client = client or _get_client()
    prompt_user = user
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt_user}],
                response_format={"type": "json_object"},
                temperature=0.2,
                reasoning_effort="low",
                max_completion_tokens=max_completion_tokens,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise ValueError(f"LLM returned empty content (finish_reason={response.choices[0].finish_reason})")
            return json.loads(content)
        except (json.JSONDecodeError, ValueError, Exception) as exc:
            last_error = exc
            if attempt < max_attempts:
                prompt_user = user + prompts.RETRY_SUFFIX
                time.sleep(2**attempt)

    raise RuntimeError(f"LLM call did not return valid JSON after {max_attempts} attempts: {last_error}") from last_error


def _format_mmss(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60}:{total % 60:02d}"


def _split_words(text: str, chunk_chars: int) -> list[str]:
    """Word-boundary chunking — good enough for feeding a prose transcript
    through a fixed-size prompt; a mid-conversation split occasionally
    landing inside one thought is an acceptable cost given the extraction
    prompt is asked to pull independent decision/commitment lines anyway."""
    words = text.split()
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_chars:
            pieces.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        pieces.append(" ".join(current))
    return pieces


# ---------------------------------------------------------------------------
# Speaker-turn segmentation — LLM-inferred from context, not verified
# diarization (Whisper has no speaker identity). Batched so each call's
# prompt stays small enough to fit the account's per-minute token budget
# regardless of overall meeting length.
# ---------------------------------------------------------------------------

DIARIZE_BATCH_SIZE = 60
DIARIZE_MAX_COMPLETION_TOKENS = 3000
# Meetings with more segments than this skip diarization entirely rather
# than run an unbounded number of batched calls — the transcript still
# displays fine as plain text via the existing full_text fallback.
MAX_DIARIZE_SEGMENTS = 1200


def diarize_segments(segments: list[dict]) -> list[dict]:
    """Returns [{"speaker", "start", "text"}, ...] covering every input
    segment, in order. Never raises — any batch that fails to diarize falls
    back to its raw segments labeled "Unknown speaker" rather than dropping
    that stretch of the transcript from the turn view.
    """
    if not segments:
        return []
    if len(segments) > MAX_DIARIZE_SEGMENTS:
        logger.warning(
            "diarize_segments: skipping — %d segments exceeds cap of %d",
            len(segments), MAX_DIARIZE_SEGMENTS,
        )
        return []

    all_turns: list[dict] = []
    known_speakers: list[str] = []
    context_tail: list[dict] = []
    CONTEXT_TAIL_TURNS = 3

    for batch_start in range(0, len(segments), DIARIZE_BATCH_SIZE):
        batch = segments[batch_start:batch_start + DIARIZE_BATCH_SIZE]
        turns = _diarize_batch(batch, known_speakers, context_tail)
        for turn in turns:
            if turn["speaker"] not in known_speakers:
                known_speakers.append(turn["speaker"])
        all_turns.extend(turns)
        if turns:
            context_tail = turns[-CONTEXT_TAIL_TURNS:]
        if batch_start + DIARIZE_BATCH_SIZE < len(segments):
            time.sleep(2)  # spread token usage across the account's per-minute budget

    return all_turns


def _diarize_batch(segments: list[dict], known_speakers: list[str], context_tail: list[dict]) -> list[dict]:
    """segments here are already just this batch — indices in the prompt and
    in the parsed response are local to it."""
    fragments = "\n".join(
        f"[{i}] ({_format_mmss(seg['start'])}) {seg['text']}" for i, seg in enumerate(segments)
    )

    context_parts = []
    if known_speakers:
        context_parts.append(
            "Speakers already identified earlier in this same meeting: "
            + ", ".join(known_speakers)
            + ". Reuse one of these exact labels if this is clearly the same "
            "person speaking again; only introduce a new label for a "
            "genuinely new voice."
        )
    if context_tail:
        tail_text = "\n".join(f"{t['speaker']}: {t['text']}" for t in context_tail)
        context_parts.append(
            "The conversation immediately before this excerpt (already "
            "resolved — for continuity only, do NOT include these lines or "
            "their indices in your output):\n" + tail_text
        )
    context_block = ("\n\n".join(context_parts) + "\n\n") if context_parts else ""

    try:
        raw = _chat_json(
            prompts.DIARIZE_SYSTEM,
            prompts.DIARIZE_USER.format(context_block=context_block, fragments=fragments),
            max_completion_tokens=DIARIZE_MAX_COMPLETION_TOKENS,
            client=_get_diarize_client(),
        )
    except Exception:
        logger.exception("diarize_segments: batch of %d segments failed, falling back to unlabeled", len(segments))
        return [{"speaker": "Unknown speaker", "start": seg["start"], "text": seg["text"]} for seg in segments]

    turns_raw = raw.get("turns")
    if not isinstance(turns_raw, list):
        logger.warning("diarize_segments: batch response had no 'turns' array: %r", raw)
        return [{"speaker": "Unknown speaker", "start": seg["start"], "text": seg["text"]} for seg in segments]

    # Turns are contiguous ranges by construction — asking for a start/end
    # pair per turn (rather than an explicit index list) sidesteps a real
    # failure mode seen in testing where the model mangles a variable-length
    # list of small integers into one unparseable concatenated string.
    turns: list[dict] = []
    covered_up_to = -1
    for t in turns_raw:
        if not isinstance(t, dict):
            continue
        start_idx, end_idx = t.get("start_index"), t.get("end_index")
        if not isinstance(start_idx, int) or not isinstance(end_idx, int):
            continue
        start_idx = max(start_idx, covered_up_to + 1)
        end_idx = min(end_idx, len(segments) - 1)
        if start_idx > end_idx or start_idx < 0:
            continue

        speaker = (t.get("speaker") or "Unknown speaker").strip() or "Unknown speaker"
        text = " ".join(segments[i]["text"] for i in range(start_idx, end_idx + 1)).strip()
        if not text:
            continue
        turns.append({"speaker": speaker, "start": segments[start_idx]["start"], "text": text})
        covered_up_to = end_idx

    # any trailing segments the model never covered still need to show up
    if covered_up_to + 1 < len(segments):
        remainder_start = covered_up_to + 1
        text = " ".join(segments[i]["text"] for i in range(remainder_start, len(segments))).strip()
        if text:
            turns.append({"speaker": "Unknown speaker", "start": segments[remainder_start]["start"], "text": text})

    if not turns:
        logger.warning("diarize_segments: batch response had no usable turns: %r", raw)
        return [{"speaker": "Unknown speaker", "start": seg["start"], "text": seg["text"]} for seg in segments]

    return turns


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------

# Above this, a single extraction call's prompt tokens plus the completion
# reservation risks the same per-minute budget problem diarization hit —
# chunk the transcript instead, independent of whether audio-chunking
# (two_pass) already applies.
MAX_SINGLE_CALL_CHARS = 6000
EXTRACT_CHUNK_CHARS = 3000


def _extract_candidates(transcript_text: str) -> str:
    if len(transcript_text) <= EXTRACT_CHUNK_CHARS:
        return _chat_text(prompts.EXTRACT_SYSTEM, prompts.EXTRACT_USER.format(transcript=transcript_text))

    pieces = _split_words(transcript_text, EXTRACT_CHUNK_CHARS)
    all_candidates: list[str] = []
    for i, piece in enumerate(pieces):
        candidates = _chat_text(prompts.EXTRACT_SYSTEM, prompts.EXTRACT_USER.format(transcript=piece))
        if candidates and candidates.strip().upper() != "NONE":
            all_candidates.append(candidates)
        if i < len(pieces) - 1:
            time.sleep(2)  # spread token usage across the account's per-minute budget
    return "\n".join(all_candidates) if all_candidates else "NONE"


def summarize_transcript(transcript_text: str, two_pass: bool) -> tuple[SummaryOut, str]:
    if two_pass or len(transcript_text) > MAX_SINGLE_CALL_CHARS:
        candidates = _extract_candidates(transcript_text)
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
