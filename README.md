# Meeting Summarizer

Transcribes meeting audio and generates action-oriented summaries — a transcript, a narrative overview, key decisions, and structured action items you can check off.

Built on Groq's free, low-latency hosting of Whisper (ASR) and an open-weight 120B model (summarization), so the whole pipeline runs at **$0 cost** and processes a typical meeting in seconds, not minutes.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **ASR:** Groq — `whisper-large-v3`
- **LLM:** Groq — `openai/gpt-oss-120b`, structured JSON output
- **Frontend:** React + Vite + TypeScript, plain CSS — no UI framework, no router. Dependencies were kept to only what each piece strictly needs throughout (no Alembic, no Celery/Redis, no Tailwind) — see the build-plan artifact linked below for the reasoning.

## Setup

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows: copy, macOS/Linux: cp
```

Fill in `GROQ_API_KEY` in `.env` — a free key from https://console.groq.com (no card required).

**ffmpeg is also required** (long-audio chunking and duration detection) — install it and make sure it's on your PATH:
- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` (or your distro's equivalent)

Run the API:

```bash
uvicorn app.main:app --reload --app-dir .
```

Docs at http://127.0.0.1:8000/docs. `GET /api/health` should return `{"status": "ok"}`.

**Frontend:**

```bash
cd frontend
npm install
copy .env.example .env        # Windows: copy, macOS/Linux: cp
npm run dev
```

Opens at http://localhost:5173. Expects the backend running at `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`) — start the backend first.

## How it works

1. Upload an audio file. Short/small ones start transcribing immediately.
2. A meeting over **15 minutes or 20MB** stops at `pending_confirmation` instead of processing automatically — the frontend shows a warning ("This meeting is about 18 min long... Continue?") and waits for you to accept before anything runs.
3. Groq transcribes the audio — chunked on silence and stitched back together for long meetings, transcribing up to 3 chunks concurrently (stays under Groq's per-file limit and the free-tier rate limit at the same time).
4. Groq summarizes the transcript into an overview, key decisions, and action items as validated, schema-checked JSON. Long/chunked meetings automatically use a two-pass extract-then-structure prompt instead of a single pass — see *Prompt design* below for why.
5. Status moves through `uploaded → transcribing → transcribed → summarizing → completed`, or `failed` with a specific error message at whichever stage broke. The frontend polls and updates live.

## Prompt design

Prompts live in `backend/app/prompts/v1.py`, versioned and logged per summary (`summaries.prompt_version`) so different prompt versions are traceable in the data, not just in commit history.

Two strategies, chosen automatically by meeting length:

- **Single-pass** (short meetings): one call asks for the full structured JSON directly from the transcript.
- **Two-pass, extract-then-structure** (meetings that triggered chunking): a first call pulls quoted candidate decisions/commitments out of the transcript; a second call structures those into the final JSON. Splitting extraction from formatting measurably improves recall on long or messy transcripts — but this was tuned by hand: the first version quoted lines without the speaker's name attached, so every action item lost its owner. Fixed by requiring the extraction prompt to preserve the speaker label and enough surrounding context per line.

Both prompts explicitly instruct the model not to invent decisions, names, or dates — verified by hand: a chit-chat transcript with no real decisions correctly comes back with empty arrays, and the model correctly refuses to guess an ISO due-date from a relative term like "Friday" when no reference date is available, rather than hallucinating one.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Tests run against an isolated temp SQLite database (never the dev `app.db`) and mock the Groq calls, so they run in well under a second with no API key or network access needed. Coverage: upload validation, the full auto-processing pipeline (mocked ASR/LLM), failure-path error messages, the confirmation-gate 409/404s, action-item PATCH validation, and delete.

## API

| Route | Description |
|---|---|
| `POST /api/meetings` | Upload audio (multipart, field `file`, optional `title`). Auto-starts processing, or returns `pending_confirmation` for long/large files. |
| `POST /api/meetings/{id}/confirm-processing` | Accept the chunked-processing warning and start the background job. |
| `GET /api/meetings` | List all meetings. |
| `GET /api/meetings/{id}` | Fetch one meeting (status, size/duration, error). |
| `GET /api/meetings/{id}/transcript` | The stitched transcript. 404 until transcription finishes. |
| `GET /api/meetings/{id}/summary` | Overview, key decisions, and action items. 404 until summarization finishes. |
| `PATCH /api/action-items/{id}` | Toggle `open`/`done`, edit `owner` or `due_date`. |
| `DELETE /api/meetings/{id}` | Removes the meeting, its audio file, transcript, and summary. |

`POST /api/meetings/{id}/reprocess` (retry a failed meeting without re-uploading) was scoped out to keep the surface area focused on what the assignment brief asks for — deleting and re-uploading covers the same need for a demo-scale project.

## Frontend

Two views, switched by local state rather than a router — one more dependency wasn't worth it for two screens:

- **Dashboard** — drag-and-drop upload, meeting list with live-polling status pills (polling stops automatically once nothing's actively processing)
- **Meeting detail** — the confirmation banner for long/large meetings, a processing spinner, then summary + checkable action items + transcript once ready, and a delete option

## Known limitations

- **No speaker diarization.** Whisper's transcription API doesn't separate speakers; the transcript is a single stream. Decisions/action-item owners are inferred by the LLM from conversational context (who says "I'll do X"), which worked correctly in testing but isn't as reliable as ground-truth diarization would be.
- **Single-user, no auth.** Matches the assignment's brief; anyone with API access can see all meetings.
- **Groq free-tier rate limits.** Fine for a demo; heavy concurrent use would need backoff tuning beyond the current 3-chunk concurrency cap.
- **SQLite.** Fine for a demo; the SQLAlchemy models are swappable to Postgres via `DATABASE_URL` with no code changes if this needed to scale.

## Demo video

_[Add link here after recording — see the shared build-plan artifact for a suggested recording script.]_
