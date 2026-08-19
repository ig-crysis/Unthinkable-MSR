# Meeting Summarizer

Transcribes meeting audio and generates action-oriented summaries — a transcript, a narrative overview, key decisions, and structured action items.

Built on Groq's free, low-latency hosting of Whisper (ASR) and an open-weight Llama-class model (summarization), so the whole pipeline runs at $0 cost.

> **Status:** Phase 4 (frontend) complete. Full app is functional end-to-end — upload, transcribe, summarize, and review, all from the browser. This README grows with each phase.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **ASR:** Groq — `whisper-large-v3`
- **LLM:** Groq — `openai/gpt-oss-120b` (structured JSON output)
- **Frontend:** React + Vite + TypeScript, plain CSS (no UI framework — see *Project structure* in the build plan for why)

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows: copy, macOS/Linux: cp
```

Fill in `GROQ_API_KEY` in `.env` — a free key from https://console.groq.com (no card required). Required from this phase onward.

**ffmpeg is also required** (used for long-audio chunking and duration detection) — install it and make sure it's on your PATH:
- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` (or your distro's equivalent)

Run the API:

```bash
uvicorn app.main:app --reload --app-dir .
```

Docs at http://127.0.0.1:8000/docs. `GET /api/health` should return `{"status": "ok"}`.

## Frontend setup

```bash
cd frontend
npm install
copy .env.example .env        # Windows: copy, macOS/Linux: cp
npm run dev
```

Opens at http://localhost:5173. Expects the backend running at `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`) — start the backend first.

## How it works

1. Upload an audio file. Short/small ones start transcribing immediately.
2. A meeting over **15 minutes or 20MB** stops at `pending_confirmation` instead of processing automatically — the response includes a `processing_note` ("This meeting is about 18 min long... Continue?") meant for a frontend confirm prompt. Nothing runs until you call `confirm-processing`.
3. Once processing starts: Groq transcribes the audio (chunked + stitched for long meetings, via ffmpeg silence-detection splitting run at up to 3 chunks concurrently), then Groq summarizes the transcript into an overview, key decisions, and action items, returned as validated structured JSON.
4. Meeting status moves through `uploaded → transcribing → transcribed → summarizing → completed`, or `failed` with an error message at whichever stage broke.

## API (current)

| Route | Description |
|---|---|
| `POST /api/meetings` | Upload audio (multipart, field `file`, optional `title`). Auto-starts processing, or returns `pending_confirmation` for long/large files. |
| `POST /api/meetings/{id}/confirm-processing` | Accept the chunked-processing warning and start the background job. |
| `GET /api/meetings` | List all meetings. |
| `GET /api/meetings/{id}` | Fetch one meeting (status, size/duration, error). |
| `GET /api/meetings/{id}/transcript` | The stitched transcript. 404 until transcription finishes. |
| `GET /api/meetings/{id}/summary` | Overview, key decisions, and action items. 404 until summarization finishes. |
| `PATCH /api/action-items/{id}` | Toggle `open`/`done`, edit `owner` or `due_date`. |

`POST /api/meetings/{id}/reprocess` and `DELETE /api/meetings/{id}` land in a later phase.

## Frontend

Two views, no router (kept out to minimize dependencies for a two-screen app):

- **Dashboard** — drag-and-drop upload, meeting list with live-polling status pills
- **Meeting detail** — the confirmation prompt for long/large meetings, a processing spinner, then the summary (overview, key decisions, a checkable action-item list) and full transcript once ready

Polling stops automatically once nothing is actively processing.
